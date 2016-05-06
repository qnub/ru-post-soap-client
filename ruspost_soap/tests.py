# -*- coding: utf-8 -*-

import unittest

from client import RuPostClient, MakeTicketException
from test_data import TRACKS, TICKETS


class RuPostClientTest(unittest.TestCase):
    def test_fail_auth(self):
        if not TRACKS:
            raise AssertionError('Не заданы номера треков для теста')

        client = RuPostClient('login', 'pass')

        self.assertRaises(MakeTicketException, client.make_ticket, TRACKS)

    def test_ticket_creation(self):
        """
        Внесите в test_data номера треков для теста.
        """
        if not TRACKS:
            raise AssertionError('Не заданы номера треков для теста')

        client = RuPostClient()

        answer = client.make_ticket(TRACKS)

        ticket_number = answer.keys()[0]
        tracks = answer.values()[0]

        self.assertTrue(isinstance(ticket_number, basestring))
        self.assertTrue(set(TRACKS) >= set(tracks))

        print u'Тикет: {0} используйте в списке TICKETS в `test_data`'.format(
            ticket_number)

    def test_track_request(self):
        """
        Внесите в test_data номер тикета полученный в тесте
        self.test_ticket_creation.
        """
        if not TICKETS:
            raise AssertionError('Не заданы номера тикетов для теста')

        client = RuPostClient()

        answer = client.get_tracks(TICKETS)

        self.assertTrue(isinstance(answer, dict))

        print u'\n\nОТВЕТ по тикетам:\n{0}\n\n'.format(answer)


if __name__ == '__main__':
    unittest.main()
