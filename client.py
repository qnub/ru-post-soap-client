# -*- coding: utf-8 -*-


from datetime import datetime
from collections import Iterable

from suds.client import Client

import settings


RPOST_LOGIN = settings.RPOST_LOGIN
RPOST_PASSWORD = settings.RPOST_PASSWORD
RPOST_WSDL_URL = settings.RPOST_WSDL_URL
RPOST_TRACK_PER_TICKET = settings.RPOST_TRACK_PER_TICKET

if RPOST_TRACK_PER_TICKET > 3000:  # ограничение сервиса
    RPOST_TRACK_PER_TICKET = 3000

if not RPOST_WSDL_URL:
    RPOST_WSDL_URL = 'http://vfc.russianpost.ru:8080/FederalClient/' \
                                                        'ItemDataService?wsdl'

RPOST_OPERTYPEIDS = {  # также в текстовом виде в operation._OperName
    1: u'Приём',
    2: u'Вручение',
    3: u'Возврат',
    4: u'Досылка почты',
    5: u'Невручение',
    6: u'Хранение',
    7: u'Временное хранение',
    8: u'Обработка',
    9: u'Импорт международной почты',
    10: u'Экспорт международной почты',
    11: u'Передано таможне',
    12: u'Неудачная попытка вручения',
    13: u'Регистрация отправки',
    14: u'Таможенное оформление завершено',
    15: u'Передача на временное хранение',
    16: u'Уничтожение',
}
RPOST_OPERCTGIDS = {
    0: u'Сортировка',
    1: u'Вручение адресату',  # Выпущено таможней при 14 типе
    2: u'Прибыло в место вручения',  # Партионный при 1 типе
    3: u'Прибыло в сортировочный центр',
    4: u'Покинуло сортировочный центр',
    5: u'Прибыло в место международного обмена',
    6: u'Покинуло место международного обмена',
    8: u'Иное',
    9: u'Адресат заберет отправление сам',
    10: u'Нет адресата',
}


class MakeTicketException(Exception):
    """
    Ошибка создания тикета.
    """
    def __init__(self, number='', message=''):
        self.number = number
        self.message = message

    def __unicode__(self):
        return u'[{0}] {1}'.format(self.number, self.message)


class UnrecognizedAnswer(MakeTicketException):
    """
    Неопознанный ответ сервиса при создании тикета.
    """


class RuPostClient(object):
    """
    Russian Post SOAP API client.
    """

    def __init__(self, login='', password='', url='', tracks_per_ticket=0):
        """
        :param login: - логин на сервисе Почты России
        :param password: - пароль на сервисе Почты России
        :param url: - url к wsdl описанию сервиса
        :param tracks_per_ticket: - количество треков на тикет (не более 3000)
        """
        self.login = login if login else RPOST_LOGIN
        self.password = password if password else RPOST_PASSWORD
        self.url = url if url else RPOST_WSDL_URL
        self.tracks_per_ticket = tracks_per_ticket if tracks_per_ticket and \
                        tracks_per_ticket <= 3000 else RPOST_TRACK_PER_TICKET

        if not self.tracks_per_ticket:
            self.tracks_per_ticket = 100

        self.client = Client(self.url)

    def get_tracks(self, tickets):
        """
        Загрузка данных трекинга отправлений по ранее созданному тикету.
        """
        ticket_status = {}

        for ticket in tickets:
            answer = self.client.service.getResponseByTicket(ticket=ticket,
                login=self.login, password=self.password)

            error = getattr(answer, 'error', None)

            if error:
                error_number = getattr(error, '_ErrorTypeID', '')
                error_text = unicode(getattr(error, '_ErrorName', ''))

                ticket_status[ticket] = {'error': (error_number,
                                                    error_text)}
                continue

            tracks = []

            for item in answer.value.Item:
                barcode = unicode(item._Barcode)
                item_error = getattr(item, 'Error', None)

                if item_error:
                    if isinstance(item_error, Iterable):
                        item_error = item_error[0]

                    item_error_number = getattr(item_error, '_ErrorTypeID', '')
                    item_error_text = unicode(getattr(item_error, '_ErrorName',
                      ''))
                    tracks.append(
                        {
                            barcode: {
                                'error': (
                                    item_error_number,
                                    item_error_text
                                )
                            }
                        }
                    )
                    continue

                operations = getattr(item, 'Operation', [])
                data = []

                for operation in operations:
                    oper_name = unicode(operation._OperName)

                    data.append(dict(
                        oper_type=operation._OperTypeID,
                        oper_ctg=operation._OperCtgID,
                        operation=oper_name,
                        date=datetime.strptime(operation._DateOper,
                            "%d.%m.%Y %H:%M:%S"),
                        zipcode=unicode(operation._IndexOper),
                        attribute=RPOST_OPERCTGIDS.get(
                            operation._OperCtgID, str(
                              operation._OperCtgID))
                    ))

                tracks.append(
                    {
                        barcode: {'data': data}
                    }
                )

            ticket_status[ticket] = tracks

        return ticket_status

    def _make_ticket(self, tracks):
        """
        Выполнение запроса на создание тикета для части треков.
        """
        timestamp = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
        track_set = []

        for track in tracks:
            item = self.client.factory.create('item')
            item._Barcode = track.strip()
            track_set.append(item)

        req_file = self.client.factory.create('file')

        req_file._DatePreparation = timestamp
        req_file._FileTypeID = '1'
        req_file._FileNumber = '0'
        req_file._SenderID = '0'
        req_file._RecipientID = '1'
        req_file.Item = track_set

        result = self.client.service.getTicket(request=req_file,
            login=self.login, password=self.password)

        ticket_number = getattr(result, 'value', None)

        if ticket_number:
            return unicode(ticket_number)
        else:
            error = getattr(result, 'error', None)

            if error:
                error_number = getattr(error, '_ErrorTypeID', '')
                error_text = unicode(getattr(error, '_ErrorName', ''))

                raise MakeTicketException(error_number, error_text)
            else:
                raise UnrecognizedAnswer()

    def make_ticket(self, tracks):
        """
        Создание тикетов по трекам.
        """
        tickets = {}
        tracks = list(tracks)
        track_set = tracks[:self.tracks_per_ticket]

        while track_set:
            tickets[self._make_ticket(track_set)] = track_set
            del tracks[:self.tracks_per_ticket]
            track_set = tracks[:self.tracks_per_ticket]

        return tickets
