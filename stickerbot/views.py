import time
import random
from operator import itemgetter
from django.http import JsonResponse
from django.views.generic.base import View
from .models import Chat, Sticker, Intermediate
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from .api import Update
from pprint import pprint
from .languages import LANG



class Bot(View):
    http_method_names = ['post']

    def post(self, request):
        upd = Update(request)
        if upd.type == 'message':
            self.msg = upd.get_message()
            self.chat = self.get_or_create_chat(self.msg.chat)
            # do not reply to message if it's old but save any posted stickers
            if (time.time() - self.msg.date) > 300:
                if self.msg.type == 'sticker':
                    self.save_sticker()
                return JsonResponse({})
            self.lang = LANG[self.chat.lang]
            self.rand_gen = random.SystemRandom()
            if self.chat.binding_word:
                if self.msg.type == 'sticker':
                    sticker_obj = self.save_sticker()
                    data = self.create_word_binding(sticker_obj)
                else:
                    data = self.msg.text_response(self.lang['not_sticker'],
                                              reply=True)
                self.chat.binding_word = ''
                self.chat.save()
                return JsonResponse(data)
            msg_types_map = {
                'left_chat_member': self.handle_left,
                'new_chat_member': self.handle_new,
                'text': self.handle_text,
                'sticker': self.handle_sticker,
            }
            try:
                method = msg_types_map[self.msg.type]
                data = method()
            except KeyError:
                data = self.send_random(prob=True)
        elif upd.type == 'callback_query':
            self.call_query = upd.get_callback_query()
            msg = self.call_query.get_message()
            self.chat = self.get_or_create_chat(msg.chat)
            data = self.change_language()
        # ignores any junk data, edited messages etc.
        else:
            data = {}
        return JsonResponse(data)

    def get_or_create_chat(self, chat):
        try:
            chat_inst = Chat.objects.get(chat_id=chat.id)
        except ObjectDoesNotExist:
            chat_name = chat.name
            chat_inst = Chat(chat_id=chat.id, name=chat_name)
            chat_inst.save()
        return chat_inst

    # formatting could be added
    def stats(self, *args):
        count = self.chat.stickers.distinct().count()
        binds = self.chat.intermediate_set.exclude(word='').values_list('word', flat=True)
        binds = ', '.join(sorted(binds))
        text = self.lang['stats'].format(count, binds)
        return self.msg.text_response(text)

    def set_chance(self, *args):
        low, high = 0, 50
        try:
            str_num = args[0]
            num = float(str_num)
        except(IndexError, ValueError):
            text = self.lang['set_chance_junk'].format(low, high)
        else:
            if low <= num <= high:
                prob = num / 100
                self.chat.probability = prob
                self.chat.save()
                text = self.lang['set_chance_success'].format(str_num)
            else:
                text = self.lang['set_chance_limit'].format(low, high)
        return self.msg.text_response(text)

    def handle_left(self):
        if self.msg.get_left_member_username() == settings.BOT_USERNAME:
            self.chat.delete()
            data = {}
        else:
            data = self.send_random()
        return data

    def handle_new(self):
        if self.msg.get_new_member_username() == settings.BOT_USERNAME:
            data = self.send_language_choices()
        else:
            data = self.send_random()
        return data

    def handle_text(self):
        methods_map = {
            '/pshh': self.send_random, '/chance': self.set_chance,
            '/bind': self.initialize_bind, '/unbind': self.unbind,
            '/stats': self.stats,
            '/help': self.show_help,
            '/language': self.send_language_choices

        }
        command, args = False, ()
        if self.msg.is_command():
            command, args = self.msg.get_command()
        if command in methods_map:
            method = methods_map[command]
            data = method(*args)
        else:
            text = self.msg.get_text().lower()
            words = self.chat.intermediate_set.exclude(word='')
            words = words.values_list('word', 'sticker__sticker_id')
            matches = []
            for word, sticker in words:
                ind = text.find(word)
                if ind != -1:
                    matches.append((word, sticker, ind))
            if matches:
                matches.sort(key=lambda x: len(x[0]), reverse=True)
                matches.sort(key=itemgetter(2))
                stick_id = matches[0][1]
                data = self.msg.get_sticker_resp(stick_id, reply=settings.REPLY)
            else:
                data = self.send_random(prob=True)
        return data

    def handle_sticker(self):
        data = self.send_random(prob=True)
        self.save_sticker()
        return data

    def send_random(self, *args, prob=False):
        if prob:
            if not self.rand_gen.random() <= self.chat.probability:
                return {}
        count = self.chat.stickers.distinct().count()
        if count <= 25:
            query_args = ('standard', self.chat.chat_id)
        else:
            query_args = (self.chat.chat_id,)
        stickers = Sticker.objects.filter(chat__chat_id__in=query_args).distinct()
        stickers = stickers.values_list('sticker_id', flat=True)
        try:
            rand_sticker_id = random.choice(stickers)
            data = self.msg.get_sticker_resp(rand_sticker_id, reply=settings.REPLY)
        except IndexError:
            data = {}
        return data

    def save_sticker(self):
        sticker_id = self.msg.get_sticker_id()
        try:
            sticker = Sticker.objects.get(sticker_id=sticker_id)
        except ObjectDoesNotExist:
            sticker = Sticker.objects.create(sticker_id=sticker_id)
        in_chat = self.chat.stickers.filter(sticker_id=sticker_id).exists()
        if not in_chat:
            Intermediate.objects.create(chat=self.chat, sticker=sticker)
        return sticker

    def create_word_binding(self, sticker):
        binding = self.chat.binding_word.lower()
        query = Intermediate.objects.filter(chat=self.chat, word=binding)
        if query.exists():
            query.update(sticker=sticker)
        else:
            Intermediate.objects.create(chat=self.chat, sticker=sticker, word=binding)
        text = self.lang['bind_success']
        return self.msg.text_response(text)

    def initialize_bind(self, *args):
        if args:
            word = ' '.join(args)
            self.chat.binding_word = word
            self.chat.save()
            text = self.lang['bind_init']
        else:
            text = self.lang['bind_empty']
        return self.msg.text_response(text)

    def unbind(self, *args):
        if args:
            word = ' '.join(args)
            res = Intermediate.objects.filter(chat=self.chat, word=word).delete()
            text = self.lang['unbind_success']
            if not res[0]:
                text = self.lang['unbind_junk'].format(word)
        else:
            text = self.lang['unbind_empty']
        return self.msg.text_response(text)

    def send_language_choices(self, *args):
        text = self.lang['choose_language']
        reply_markup = {
            'inline_keyboard': [[
                {'text': 'English', 'callback_data': 'english'},
                {'text': 'Русский', 'callback_data': 'russian'}
            ]],
        }
        return self.msg.text_response(text, reply_markup=reply_markup)

    def change_language(self):
        lang = self.call_query.data
        self.chat.lang = lang
        self.chat.save()
        text = LANG[lang]['language_changed']
        return self.call_query.change_inline_msg(text)

    def show_help(self):
        text = self.lang['help']
        msg = self.msg.text_response(text, markdown='HTML')
        msg['disable_web_page_preview'] = True
        return msg

    # def send_help_msg(self, *args):
    #     text = self.lang('help')
    #     return self.msg.text_response(text, markdown='Markdown')
