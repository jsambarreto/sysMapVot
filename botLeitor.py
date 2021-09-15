# -*- coding: utf-8 -*-

# Telegram
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, Filters, MessageHandler, CallbackContext
# QR Code
from pyzbar.pyzbar import decode

# System libraries
import os
from os import listdir
from os.path import isfile, join
import config
import json
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

from io import BytesIO
from PIL import Image
from random import randint

FB = json.loads(os.environ.get('FIREBASE_CREDENTIALS', None))
cred = credentials.Certificate(FB)
#cred = credentials.Certificate('registra-urna-firebase-adminsdk-le28m-70d82a58ae.json')
firebase_admin.initialize_app(cred)

db = firestore.client()

#TOKEN = config.TOKEN
TOKEN = os.environ.get('TOKEN', None)
base = []
if __name__ == '__main__':
    
    def gerarIdLeitura():
        return randint(0,1000)*58

    def decode_qr(update: Update, context: CallbackContext):
        chat_id = update.message.chat_id

        if update.message.photo:
            id_img = update.message.photo[-1].file_id
        else:
            return

        foto = context.bot.getFile(id_img)

        new_file = context.bot.get_file(foto.file_id)
        new_file.download('qrcode.png')

        try:
            arq = open('base2.csv', 'a')
            x = gerarIdLeitura()
            result = decode(Image.open('qrcode.png'))
            base.append(result[0].data.decode("utf-8"))
            context.bot.sendMessage(chat_id=chat_id, text='Em processamento')
            os.remove("qrcode.png")
            arq.write(result[0].data.decode("utf-8"))
            arq.write('\n')
            arq.close()
            
            doc_ref = db.collection(u'urnas_bahia').document(str(x))
            error = 0
            for campo in result[0].data.decode("utf-8").split(' '):
                chave = campo.split(':') 
                if chave[0] == 'HASH':
                    doc_pesq = db.collection(u'urnas_bahia').stream()
                    doc_list = []
                    for doc in doc_pesq:
                        doc_list.append(f'{doc.id}')
                    hash = chave[1]
                    for doc_ in doc_list:
                        doc_ref_ = db.collection(u'urnas_bahia').document(doc_)
                        doc_l = doc_ref_.get()
                        doc_aux = doc_l.to_dict()
                        campo_ = 'HASH'
                        if doc_aux.get(campo_) == hash:
                            db.collection(u'urnas_bahia').document(str(x)).delete()                       
                            context.bot.sendMessage(chat_id=chat_id, text='QR Code já lido')
                            error = 1
                if chave[0] != 'QRBU':
                    a, b = chave
                    doc_ref.set({
                    str(a): b,
                    },merge = True)
                else:
                    a,b,c = chave
                    doc_ref.set({
                    str(a): b+c,
                    },merge = True) 
                
            if error == 0:
                context.bot.sendMessage(chat_id=chat_id, text='QR Code lido com sucesso')
        except Exception as e:
            context.bot.sendMessage(chat_id=chat_id, text='Não foi possivel identificar o QRCode, tente novamente.')
            #os.remove("qrcode.png")

    #def main():
    updater = Updater(TOKEN, request_kwargs={'read_timeout': 20, 'connect_timeout': 20}, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(MessageHandler(Filters.photo, decode_qr))

    updater.start_polling()
    updater.idle()