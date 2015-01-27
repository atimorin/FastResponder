# -*- coding: utf-8 -*-
"""
Created on Mon Dec  9 15:16:16 2013

@author: slarinier
"""
###############################################################################
#
#   FastResponder - Collect artefacts Windows for First Reponder
#    cert@sekoia.fr - http://www.sekoia.fr
#   Copyright (C) 2014  SEKOIA
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from __future__ import unicode_literals
import win32evtlog, win32evtlogutil, win32con, winerror
from utils import get_csv_writer, write_to_csv
import datetime

# UserID is a SID to convert
hevt_to_write = {'Channel':'', 'EventID':'', 'Execution':'ProcessID', 'Level':'', 'Provider':'Name', 'Security':'UserID', 'TimeCreated':'SystemTime'}

class _EventLogs(object):
	def __init__(self, params):
		self.output_dir=params['output_dir']
		self.computer_name = params['computer_name']
		self.logger=params['logger']
	
	def _list_evt_Vista(self, server, logtype):
		''' Retrieves the contents of the event log '''
		try:
			self.logger.info('Processing evtx : ' + logtype)
			win32evtlog.EvtExportLog(logtype, self.output_dir + '\\' + self.computer_name + '_' + logtype.replace('/', '_') + '.evtx', 1)
		except:
			self.logger.error('Error while processing evtx : ' + logtype)
		
	def _list_evt_XP(self, server, logtype):
		hand = win32evtlog.OpenEventLog(server,logtype)
		flags = win32evtlog.EVENTLOG_FORWARDS_READ|win32evtlog.EVENTLOG_SEQUENTIAL_READ
		total = win32evtlog.GetNumberOfEventLogRecords(hand)
		sum_evt=0
		while True:
			events = win32evtlog.ReadEventLog(hand, flags,0)
			sum_evt += len(events)
			if events:
				for event in events:
					data = event.StringInserts
					date = datetime.datetime(event.TimeGenerated.year, event.TimeGenerated.month, event.TimeGenerated.day, event.TimeGenerated.hour, event.TimeGenerated.minute, event.TimeGenerated.second).strftime('%d/%m/%Y %H:%M:%S')
					
					#print date + ' : ' + log_type + ' -> ' + log_data
					if data: 
						yield unicode(event.EventCategory), unicode(event.SourceName), unicode(event.EventID), unicode(event.EventType), date, list(data)
					else:
						yield unicode(event.EventCategory), unicode(event.SourceName), unicode(event.EventID), unicode(event.EventType), date, []
			if sum_evt >= total:
				break
	
	def _csv_event_logs(self, isWinXP):
		''' Prints the event logs in a csv, the called method is different for WinXP and lower '''
		server = None # name of the target computer to get event logs, None to get logs from current computer
		with open(self.output_dir + '\\' + self.computer_name + '_evts.csv', 'wb') as fw:
			csv_writer = get_csv_writer(fw)
			if isWinXP:
				for eventCategory, sourceName, eventID, eventType, date, log in self._list_evt_XP(server, 'Security'):
					write_to_csv([self.computer_name, 'Logs', 'Security', eventCategory, sourceName, eventID, eventType, date] + log, csv_writer)
				for eventCategory, sourceName, eventID, eventType, date, log in self._list_evt_XP(server, 'Application'):
					write_to_csv([self.computer_name, 'Logs', 'Application', eventCategory, sourceName, eventID, eventType, date] + log, csv_writer)
				for eventCategory, sourceName, eventID, eventType, date, log in self._list_evt_XP(server, 'System'):
					write_to_csv([self.computer_name, 'Logs', 'System', eventCategory, sourceName, eventID, eventType, date] + log, csv_writer)
			else:
				# Exports everything from the event viewer
				evt_handle = win32evtlog.EvtOpenChannelEnum()
				while True:
					# opening channel for enumeration
					logtype = win32evtlog.EvtNextChannelPath(evt_handle)
					if logtype is None:
						break
					#fw.write('"Computer Name"|"Type"|"Date"|"logtype"|"log data"\n')
					self._list_evt_Vista(server, logtype)
		