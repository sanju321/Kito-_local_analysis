from __future__ import division
import urllib2
import wx
import csv
import os
import sys
import time
import requests
import wx.calendar as cal
import operator
from threading import *
from datetime import datetime

start_date_picked = ''
end_date_picked = ''
csv_list = []  # used for storing file data
charger_csv_list = []  # used for storing file data
pcba_csv_list = []
down_csv_list = []

rowheader_sort_csv = []
# row_header=['sid','ecg','encryption_bit','charging_res','temp','firmware_imgB_version','fuelgauge','spo2','time','overall_res','date','mac','sn','device_class','firmware_imgA_version','battery_per']
row_header = []  # store first row of csv file in list
charger_row_header = []  # store first row of csv file in list
pcba_row_header = []
down_row_header = []

first_load_click = True  # load buuton click more than once
charger_first_load_click = True  # load buuton click more than once

pcba_first_load_click = True  # load buuton click more than once
ID_DOWNLOAD = wx.NewId()
ID_START_DATE = wx.NewId()
ID_END_DATE = wx.NewId()

# Define notification event for thread completion
EVT_RESULT_ID = wx.NewId()
EVT_START_DATE_ID = wx.NewId()
EVT_END_DATE_ID = wx.NewId()


def EVT_RESULT(win, func):
    """Define Result Event."""
    win.Connect(-1, -1, EVT_RESULT_ID, func)


def EVT_START_DATE(win, func):
    """Define Result Event."""
    win.Connect(-1, -1, EVT_START_DATE_ID, func)


def EVT_END_DATE(win, func):
    """Define Result Event."""
    win.Connect(-1, -1, EVT_END_DATE_ID, func)


class ResultEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""

    def __init__(self, data, data2):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_RESULT_ID)
        self.data = data
        self.data2 = data2


class StartDateEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""

    def __init__(self, data):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_START_DATE_ID)
        self.data = data


class EndDateEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""

    def __init__(self, data):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_END_DATE_ID)
        self.data = data


# Thread class that executes processing
class WorkerThread(Thread):
    """Worker Thread Class."""

    def __init__(self, notify_window, start_date_list, end_date_list, project_to_download):
        """Init Worker Thread Class."""
        Thread.__init__(self)
        self._notify_window = notify_window
        self.start_date_list = start_date_list
        self.end_date_list = end_date_list
        self._want_abort = 0
        self._internet_abort = 0
        self.project_to_download = project_to_download
        # This starts the thread running on creation, but you could
        # also make the GUI thread responsible for calling this
        self.start()

    # def sort_csv(self,csv_filename, types, sort_key_columns):

    #    data = []

    #    first_sort_csv=True
    #    with open(csv_filename, 'rb') as f:
    #        for row in csv.reader(f):
    #            if first_sort_csv:
    #                first_sort_csv=False
    #                rowheader_sort_csv.append(row)
    #            else:
    #                data.append(self.convert(types, row))

    #        #print data
    #    data.sort(key=operator.itemgetter(*sort_key_columns))
    #    print rowheader_sort_csv
    #    with open(csv_filename, 'wb') as f:
    #        csv.writer(f).writerows(rowheader_sort_csv)
    #        csv.writer(f).writerows(data)

    # def convert(self,types, values):
    #    return [t(v) for t, v in zip(types, values)]


    def sort_csv_new(self, csv_filename, time_index, date_index):
        data = []

        first_sort_csv = True
        rowheader_sort_csv = []
        with open(csv_filename, 'rb') as f:
            for row in csv.reader(f):
                if first_sort_csv:
                    first_sort_csv = False
                    rowheader_sort_csv.append(row)
                else:
                    data.append(row)


        # for i in range(len(data)):
        # 	conv=time.strptime(data[i][date_index],"%b %d %Y")
        # 	data[i][date_index]=time.strftime("%m/%d/%Y",conv)
        # #print data


        data.sort(key=lambda date: datetime.strptime(date[time_index] + date[date_index], "%H:%M:%S%b %d %Y"))
        # for i in range(len(data)):
        # 	conv=time.strptime(data[i][date_index],"%m/%d/%Y")
        # 	data[i][date_index]=time.strftime("%b %d %Y",conv)

        with open(csv_filename, 'wb') as f:
            csv.writer(f).writerows(rowheader_sort_csv)
            csv.writer(f).writerows(data)

    def reverse_csv(self, filename):
        global down_csv_list
        global down_row_header
        fi = open(filename, 'rb')
        data = fi.read()
        # print data
        fi.close()
        fo = open(filename, 'wb')
        fo.write(data.replace('\x00', ''))
        fo.close()
        f = open(filename, 'rt')
        reader = csv.reader(f)
        csv_first_row = True
        down_csv_list = []

        for row in reader:
            # print row

            if csv_first_row:
                csv_first_row = False
                down_row_header = row
            # print row_header
            else:
                down_csv_list.append(row)

        down_csv_list = down_csv_list[::-1]
        # print 'csv list::'
        # print csv_list
        f.close()

        out = open(filename, "w")  # opening csv in append mode
        output = csv.writer(out)  # getting object of csv writer
        output.writerow(down_row_header)  # writing row into csv file
        for row_append in down_csv_list:
            output.writerow(row_append)

        out.close()

    def run(self):
        # print "going to thread"
        start_date_url = str(str(self.start_date_list[2])[:4] + '-' + str(self.start_date_list[0]) + '-' + str(
            self.start_date_list[1]) + 'T' + str(time.asctime(time.localtime(time.time())).split(' ')[4]))
        end_date_url = str(str(self.end_date_list[2])[:4] + '-' + str(self.end_date_list[0]) + '-' + str(
            self.end_date_list[1]) + 'T' + str(time.asctime(time.localtime(time.time())).split(' ')[4]))

        start_date_url = str(str(self.start_date_list[2])[:4] + '-' + str(self.start_date_list[0]) + '-' + str(
            self.start_date_list[1]) + 'T00:00:00.100')
        end_date_url = str(str(self.end_date_list[2])[:4] + '-' + str(self.end_date_list[0]) + '-' + str(
            self.end_date_list[1]) + 'T23:59:59.100')

        if str(self.project_to_download) == 'System':
            f = open(
                "./System/data_" + str(self.project_to_download) + "_" + str(self.start_date_list[2])[:4] + '-' + str(
                    self.start_date_list[0]) + '-' + str(self.start_date_list[1]) + "_to_" + str(self.end_date_list[2])[
                                                                                             :4] + '-' + str(
                    self.end_date_list[0]) + '-' + str(self.end_date_list[1]) + ".csv", 'w')
            f_name = "./System/data_" + str(self.project_to_download) + "_" + str(self.start_date_list[2])[
                                                                              :4] + '-' + str(
                self.start_date_list[0]) + '-' + str(self.start_date_list[1]) + "_to_" + str(self.end_date_list[2])[
                                                                                         :4] + '-' + str(
                self.end_date_list[0]) + '-' + str(self.end_date_list[1]) + ".csv"
        if str(self.project_to_download) == 'Pcba':
            f = open(
                "./Pcba/data_" + str(self.project_to_download) + "_" + str(self.start_date_list[2])[:4] + '-' + str(
                    self.start_date_list[0]) + '-' + str(self.start_date_list[1]) + "_to_" + str(self.end_date_list[2])[
                                                                                             :4] + '-' + str(
                    self.end_date_list[0]) + '-' + str(self.end_date_list[1]) + ".csv", 'w')
            f_name = "./Pcba/data_" + str(self.project_to_download) + "_" + str(self.start_date_list[2])[
                                                                            :4] + '-' + str(
                self.start_date_list[0]) + '-' + str(self.start_date_list[1]) + "_to_" + str(self.end_date_list[2])[
                                                                                         :4] + '-' + str(
                self.end_date_list[0]) + '-' + str(self.end_date_list[1]) + ".csv"
        if str(self.project_to_download) == 'charger':
            f = open(
                "./Charger/data_" + str(self.project_to_download) + "_" + str(self.start_date_list[2])[:4] + '-' + str(
                    self.start_date_list[0]) + '-' + str(self.start_date_list[1]) + "_to_" + str(self.end_date_list[2])[
                                                                                             :4] + '-' + str(
                    self.end_date_list[0]) + '-' + str(self.end_date_list[1]) + ".csv", 'w')
            f_name = "./Charger/data_" + str(self.project_to_download) + "_" + str(self.start_date_list[2])[
                                                                               :4] + '-' + str(
                self.start_date_list[0]) + '-' + str(self.start_date_list[1]) + "_to_" + str(self.end_date_list[2])[
                                                                                         :4] + '-' + str(
                self.end_date_list[0]) + '-' + str(self.end_date_list[1]) + ".csv"

        csv_writer = csv.writer(f)

        downloaded_dct = {}
        all_download_flag = False

        strurl = "https://kito.azoi.com//accounts/login/"
        header = {
            "content-type": "application/x-www-form-urlencoded"
        }
        payload = {
            "client_id": "7vRYL8F5kQarIlqpaRZwOCHjr6Cl45",
            "grant_type": "password",
            "username": "hardik@azoi.com",
            "password": "RnD#123456"
            # "dev_id": "aBaBaBaBaBaBaBaBaBaBaBaBaBaBaBaB"
        }
        try:
            # print "getting access_token",str(self.project_to_download)
            # print start_date_url
            # print end_date_url

            r = requests.post(strurl, headers=header, data=payload)
            rJson = r.json()
            # print rJson
            access_token = rJson['results']['access_token']
            if str(self.project_to_download) == 'System':
                strurl = "https://kito.azoi.com//api/test-jig/v1/data/?from_ts=" + start_date_url + "&to_ts=" + end_date_url + "&filter=_id"
            if str(self.project_to_download) == 'Pcba':
                strurl = "https://kito.azoi.com//api/test-jig/v1/pcba_test_log/?from_ts=" + start_date_url + "&to_ts=" + end_date_url + "&filter=_id"
            if str(self.project_to_download) == 'charger':
                print "charger in"
                strurl = "https://kito.azoi.com//api/test-jig/v1/charger/test-fixture/?from_ts=" + start_date_url + "&to_ts=" + end_date_url + "&filter=_id"

            r = requests.get(strurl, headers={"Authorization": "Bearer " + access_token})
            rJson = r.json()
        # print "rJson",rJson
        except:
            # print "Internet is not working"

            self.internet_abort()
        if self._internet_abort:
            wx.PostEvent(self._notify_window, ResultEvent(-1, None))
            return
        else:

            try:
                if str(self.project_to_download) == 'System':
                    dct = rJson['results']['testjig_data']
                if str(self.project_to_download) == 'Pcba':
                    dct = rJson['results']['pcba_test_log']
                if str(self.project_to_download) == 'charger':
                    dct = rJson['results']['charger_test_fixture']


            except:
                print " Data not found"

                self.abort()

            # dlg.Destroy()
            # print "total :",len(dct)


            if self._want_abort:
                wx.PostEvent(self._notify_window, ResultEvent(None, None))
                return
            else:

                cnt = 0

                first = True
                not_processed = []
                for d in dct:
                    try:

                        if str(self.project_to_download) == 'System':
                            sid = d['testjig_data_id']
                            strurl = "https://kito.azoi.com//api/test-jig/v1/data/?testjig_data_id=" + str(sid)
                        if str(self.project_to_download) == 'Pcba':
                            sid = d['pcba_test_log_id']
                            strurl = "https://kito.azoi.com//api/test-jig/v1/pcba_test_log/?pcba_test_log_id=" + str(
                                sid)
                        if str(self.project_to_download) == 'charger':
                            sid = d['charger_test_fixture_id']
                            strurl = "https://kito.azoi.com//api/test-jig/v1/charger/test-fixture/?charger_test_fixture_id=" + str(
                                sid)
                        # print "getting data for",sid

                        r = requests.get(strurl, headers={"Authorization": "Bearer " + access_token})
                        data = r.json()
                        # print "data",data
                        if str(self.project_to_download) == 'System':
                            data1 = data['results']['testjig_data']
                        if str(self.project_to_download) == 'Pcba':
                            data1 = data["results"]["pcba_test_log"]
                        if str(self.project_to_download) == 'charger':
                            data1 = data['results']['charger_test_fixture']


                        # print "data1",data1
                        # print "downloaded_dct  ",cnt,"    ",downloaded_dct[cnt]
                        if first:
                            first = False
                            key_list = ['sid']
                            for key in data1.keys():
                                key_list.append(key)
                            csv_writer.writerow(key_list)
                        # print "data1     ",data1
                        # print "downloaded_dct values     ", downloaded_dct.values()
                        if data1 not in downloaded_dct.values():
                            downloaded_dct[cnt] = data1
                            data_l = [str(sid)]
                            for key in data1.keys():
                                data_l.append(data1[key])
                            csv_writer.writerow(data_l)
                            f.flush()
                            cnt += 1
                            wx.PostEvent(self._notify_window, ResultEvent(cnt, all_download_flag))
                    except:
                        not_processed.append(sid)
                        print "problem for fetching ", sid
                    # s = raw_input()
                # print not_processed

                for n in not_processed:
                    try:
                        sid = n
                        if str(self.project_to_download) == 'System':
                            strurl = "https://kito.azoi.com//api/test-jig/v1/data/?testjig_data_id=" + str(sid)
                        if str(self.project_to_download) == 'Pcba':
                            strurl = "https://kito.azoi.com//api/test-jig/v1/pcba_test_log/?pcba_test_log_id=" + str(
                                sid)
                        if str(self.project_to_download) == 'charger':
                            strurl = "https://kito.azoi.com//api/test-jig/v1/charger/test-fixture/?charger_test_fixture_id=" + str(
                                sid)
                        # print "getting data for",sid

                        r = requests.get(strurl, headers={"Authorization": "Bearer " + access_token})
                        data = r.json()

                        if str(self.project_to_download) == 'System':
                            data1 = data['results']['testjig_data']
                        if str(self.project_to_download) == 'Pcba':
                            data1 = data["results"]["pcba_test_log"]
                        if str(self.project_to_download) == 'charger':
                            data1 = data['results']['charger_test_fixture']
                        # print data

                        # print "downloaded_dct  ",cnt,"    ",downloaded_dct[cnt]

                        if first:
                            first = False
                            key_list = ['sid']
                            for key in data1.keys():
                                key_list.append(key)
                            csv_writer.writerow(key_list)
                        # print " data1     ",data1
                        # print "downloaded_dct values     ", downloaded_dct.values()
                        if data1 not in downloaded_dct.values():
                            downloaded_dct[cnt] = data1
                            data_l = [str(sid)]
                            for key in data1.keys():
                                data_l.append(data1[key])
                            csv_writer.writerow(data_l)
                            f.flush()
                            cnt += 1
                            wx.PostEvent(self._notify_window, ResultEvent(cnt, all_download_flag))
                    except:
                        # print "problem for fetching not processed",n
                        pass
                all_download_flag = True
                f.close()
                self.reverse_csv(f_name)
                if str(self.project_to_download) == 'System':
                    self.sort_csv_new(f_name, 8, 10)
                if str(self.project_to_download) == 'Pcba':
                    self.sort_csv_new(f_name, 11, 12)
                if str(self.project_to_download) == 'charger':
                    self.sort_csv_new(f_name, 4, 1)
                wx.PostEvent(self._notify_window, ResultEvent(cnt, all_download_flag))
            # self.sort_csv("data_sys_"+str(self.start_date_list[2])[:4]+'-'+str(self.start_date_list[0])+'-'+str(self.start_date_list[1])+"_to_"+str(self.end_date_list[2])[:4]+'-'+str(self.end_date_list[0])+'-'+str(self.end_date_list[1])+".csv",(str,str,str,str,str,str,str,str,str,str,str,str,str,str,str,str),(10,8))

    def internet_abort(self):
        self._internet_abort = 1

    def abort(self):
        """abort worker thread."""
        # Method for use by main thread to signal an abort
        self._want_abort = 1


# for dialog box
def Info(parent, message, caption='INFO', new=0):
    if new == 0:
        return
    dlg = wx.MessageDialog(parent, message, caption, wx.OK | wx.ICON_INFORMATION)
    dlg.ShowModal()
    dlg.Destroy()


# month mapping
def get_month(month):
    month_dict = {'Jan': 0,
                  'Feb': 1,
                  'Mar': 2,
                  'Apr': 3,
                  'May': 4,
                  'Jun': 5,
                  'Jul': 6,
                  'Aug': 7,
                  'Sep': 8,
                  'Oct': 9,
                  'Nov': 10,
                  'Dec': 11}
    return month_dict[month]


# split date in day month and year
def split_date(date):
    splitted = date.split(' ')
    # print splitted
    year = splitted[2]
    month = splitted[0]
    day = splitted[1]
    return day, month, year


# check whether date1 is greater than date2
def is_greater(date1, date2):
    # print date1,date2

    day1, month1, year1 = split_date(date1)
    day2, month2, year2 = split_date(date2)

    if year1 > year2:
        return True
    else:
        if year1 == year2:
            if get_month(month1) > get_month(month2):
                return True
            else:
                if get_month(month1) == get_month(month2):
                    if int(day1) > int(day2):
                        return True
                    else:
                        return False
                else:
                    return False
        else:
            return False


# #check whether date1 is greater than date2
# def is_greater(date1,date2):
#     # print date1,date2

#     day1,month1,year1 = split_date(date1)
#     day2,month2,year2 = split_date(date2)

#     if year1 < year2 or get_month(month1) < get_month(month2) or int(day1) < int(day2):
#         #print "returning false y "
#         return False
#     elif year1 > year2 or get_month(month1) > get_month(month2) or int(day1) > int(day2):
#         #print "returning false y "
#         return True
# check whether date1 is equal to date2
def is_equal(date1, date2):
    # print date1,date2

    day1, month1, year1 = split_date(date1)
    day2, month2, year2 = split_date(date2)

    if year1 == year2 and get_month(month1) == get_month(month2) and int(day1) == int(day2):
        # print "returning false y "
        return True
    else:
        return False


class Pcba_win(wx.Panel):
    def __init__(self, parent, style=wx.SIMPLE_BORDER, size=(600, 650), clearSigInt=True):

        self.dates = []
        wx.Panel.__init__(self, parent)

        self.Total_Analysis = wx.StaticBox(self, -1, 'Total Analysis', size=(800, 50), pos=(80, 40))
        self.Total_Analysis_Sizer = wx.StaticBoxSizer(self.Total_Analysis, wx.VERTICAL)

        # Total Analysis
        self.AnalysisSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.Total_Pass_Analysis = wx.StaticBox(self, -1, 'Pass Analysis', size=(800, 210), pos=(80, 90))
        self.Total_Pass_Analysis_Sizer = wx.StaticBoxSizer(self.Total_Pass_Analysis, wx.VERTICAL)

        # Pass Analysis
        self.PassAnalysisSizer = wx.BoxSizer(wx.HORIZONTAL)



        self.Overall_Fail_Analysis = wx.StaticBox(self, -1, 'Overall Fail Cycles', size=(400, 230), pos=(80, 310))
        self.Overall_Fail_Analysis_Sizer = wx.StaticBoxSizer(self.Overall_Fail_Analysis, wx.VERTICAL)

        # Overall Fail Cycles
        self.OverallFailAnalysisSizer = wx.BoxSizer(wx.HORIZONTAL)



        self.Failed_Analysis = wx.StaticBox(self, -1, 'Failed Device Fail Cycles ', size=(400, 230), pos=(480, 310))
        self.Failed_Analysis_Sizer = wx.StaticBoxSizer(self.Failed_Analysis, wx.VERTICAL)

        # Failed Device Fail Cycles
        self.FailedAnalysisSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.analyze_btn = wx.Button(self, label="Analyze", pos=(650, 10))
        self.analyze_btn.Enable(False)
        self.Bind(wx.EVT_BUTTON, self.analyze_btn_click, self.analyze_btn)

        self.load_file_btn = wx.Button(self, label="Load File", pos=(20, 10))
        self.load_file_btn.Enable(True)
        self.Bind(wx.EVT_BUTTON, self.load_file_btn_click, self.load_file_btn)

        wx.StaticText(self, -1, 'Start Date : ', (130, 10))
        self.start_date_combo_box = wx.ComboBox(self, -1, '-', pos=(220, 10), size=(120, -1), choices=self.dates,
                                                style=wx.CB_READONLY)

        wx.StaticText(self, -1, 'End Date : ', (370, 10))
        self.end_date_combo_box = wx.ComboBox(self, -1, '-', pos=(450, 10), size=(120, -1), choices=self.dates,
                                              style=wx.CB_READONLY)

        wx.StaticText(self, -1, 'Total unique devices tested: ', (100, 60))
        self.total_unique_device_tested = wx.StaticText(self, -1, '', (400, 60))

        wx.StaticText(self, -1, 'Total pass: ', (500, 60))
        self.total_pass = wx.StaticText(self, -1, '', (600, 60))

        wx.StaticText(self, -1, 'First Pass : ', (100, 120))
        self.first_pass = wx.StaticText(self, -1, '', (400, 120))

        wx.StaticText(self, -1, 'Second Pass : ', (100, 150))
        self.second_pass = wx.StaticText(self, -1, '', (400, 150))

        wx.StaticText(self, -1, 'Third Pass : ', (100, 180))
        self.third_pass = wx.StaticText(self, -1, '', (400, 180))

        wx.StaticText(self, -1, 'Fourth Pass : ', (100, 210))
        self.fourth_pass = wx.StaticText(self, -1, '', (400, 210))

        wx.StaticText(self, -1, 'Other Pass : ', (100, 240))
        self.other_pass = wx.StaticText(self, -1, '', (400, 240))

        wx.StaticText(self, -1, 'Fail Device : ', (700, 60))
        self.fail_devices = wx.StaticText(self, -1, '', (800, 60))

        wx.StaticText(self, -1, 'Fail Cycle : ', (500, 330))
        self.total_failed_cycle = wx.StaticText(self, -1, '', (800, 330))

        wx.StaticText(self, -1, 'SG_Test : ', (530, 360))
        self.sg_test_fail_in_failed_cycle = wx.StaticText(self, -1, '', (800, 360))

        wx.StaticText(self, -1, 'SD_Test : ', (530, 390))
        self.sd_test_fail_in_failed_cycle = wx.StaticText(self, -1, '', (800, 390))

        wx.StaticText(self, -1, 'Charging_test : ', (530, 420))
        self.charging_test_fail_in_failed_cycle = wx.StaticText(self, -1, '', (800, 420))

        wx.StaticText(self, -1, 'blue_led : ', (530, 450))
        self.blue_led_fail_in_failed_cycle = wx.StaticText(self, -1, '', (800, 450))

        wx.StaticText(self, -1, 'blink_led : ', (530, 480))
        self.blink_led_fail_in_failed_cycle = wx.StaticText(self, -1, '', (800, 480))

        wx.StaticText(self, -1, 'white_led : ', (530, 510))
        self.white_led_fail_in_failed_cycle = wx.StaticText(self, -1, '', (800, 510))

        wx.StaticText(self, -1, 'Retested Devices : ', (100, 270))
        self.retest_devices = wx.StaticText(self, -1, '', (400, 270))

        wx.StaticText(self, -1, 'Fail Cycle : ', (100, 330))
        self.total_fail_cycle = wx.StaticText(self, -1, '', (400, 330))

        wx.StaticText(self, -1, 'SG_Test : ', (130, 360))
        self.sg_test_fail_cycle = wx.StaticText(self, -1, '', (400, 360))

        wx.StaticText(self, -1, 'SD_Test : ', (130, 390))
        self.sd_test_fail_cycle = wx.StaticText(self, -1, '', (400, 390))

        wx.StaticText(self, -1, 'Charging_test : ', (130, 420))
        self.charging_test_fail_cycle = wx.StaticText(self, -1, '', (400, 420))

        wx.StaticText(self, -1, 'blue_led : ', (130, 450))
        self.blue_led_fail_cycle = wx.StaticText(self, -1, '', (400, 450))

        wx.StaticText(self, -1, 'blink_led : ', (130, 480))
        self.blink_led_fail_cycle = wx.StaticText(self, -1, '', (400, 480))

        wx.StaticText(self, -1, 'white_led : ', (130, 510))
        self.white_led_fail_cycle = wx.StaticText(self, -1, '', (400, 510))

        self.AnalysisSizer.Add(self.total_unique_device_tested, 0, wx.ALL | wx.CENTER, 2)
        self.AnalysisSizer.Add(self.total_pass, 0, wx.ALL | wx.CENTER, 2)
        self.AnalysisSizer.Add(self.fail_devices, 0, wx.ALL | wx.CENTER, 2)

        self.Total_Analysis_Sizer.Add(self.AnalysisSizer, 0, wx.ALL | wx.CENTER, 5)

    def reverse_csv(self, filename):
        global pcba_csv_list
        global pcba_row_header
        fi = open(filename, 'rb')
        data = fi.read()
        # print data
        fi.close()
        fo = open(filename, 'wb')
        fo.write(data.replace('\x00', ''))
        fo.close()
        f = open(filename, 'rt')
        reader = csv.reader(f)
        csv_first_row = True
        pcba_csv_list = []

        for row in reader:
            # print row

            if csv_first_row:
                csv_first_row = False
                pcba_row_header = row
            # print row_header
            else:
                pcba_csv_list.append(row)

        '''pcba_csv_list=pcba_csv_list[::-1]
        #print 'csv list::'
        print pcba_csv_list
        f.close()

        out=open(filename,"w")#opening csv in append mode
        output=csv.writer(out)#getting object of csv writer
        output.writerow(pcba_row_header)#writing row into csv file
        for row_append in pcba_csv_list:
            output.writerow(row_append)

        out.close()'''

    def analyze_btn_click(self, event):

        start_date = self.start_date_combo_box.GetValue()
        end_date = self.end_date_combo_box.GetValue()

        if is_greater(start_date, end_date):
            Info(self, "Please select valid start date and end date", "Invalid Selection", new=1)
            self.start_date_combo_box.SetValue(self.last_start_date)
            self.end_date_combo_box.SetValue(self.last_end_date)

        self.final_analysis = {}  # store all data according extracted date

        self.temp_date_list = []  # store all date from start date to end date

        if is_equal(start_date, end_date):
            for k in range(self.count):
                # print self.count
                if is_equal(start_date, self.final[k]['Date']):
                    self.final_analysis[k] = self.final[k]

        # print final_analysis
        else:
            if is_greater(end_date, start_date):
                start_index = self.dates.index(start_date)
                end_index = self.dates.index(end_date)
            # print start_index
            # print end_index
            self.temp_date_list = self.dates[start_index:end_index + 1]
            for m in range(len(self.temp_date_list)):

                for k in range(self.count):
                    if is_equal(self.temp_date_list[m], self.final[k]['Date']):
                        self.final_analysis[k] = self.final[k]

        # print self.final_analysis
        self.all_dev_dict = {'dev_addr': [], 'tested_count': [], 'overall_res': [], 'blue_led_fail': [],
                             'blink_led_fail': [], 'white_led_fail': [], 'sd_test_fail': [],
                             'charging_test_fail': [], 'sg_test_fail': [],'failed_sn':[]}
        self.dev_dict = {'dev_addr': []}

        self.blue_led_fail_cycle_counter = 0
        self.blink_led_fail_cycle_counter = 0
        self.white_led_fail_cycle_counter = 0
        self.sd_test_fail_cycle_counter = 0
        self.charging_test_fail_cycle_counter = 0
        self.sg_test_fail_cycle_counter = 0

        self.retest_counter = 0
        self.first_pass_counter = 0
        self.second_pass_counter = 0
        self.third_pass_counter = 0
        self.fourth_pass_counter = 0
        self.other_pass_counter = 0
        self.fail_devices_counter = 0

        chk_cnt = 0
        t_cnt = 0
        mac_list = []
        mac_chk_list = []
        self.fail_cycle_blue_led_dict = {}
        self.fail_cycle_blink_led_dict = {}
        self.fail_cycle_white_led_dict = {}
        self.fail_cycle_charging_test_dict = {}
        self.fail_cycle_sd_test_dict = {}
        self.fail_cycle_sg_test_dict = {}

        self.fail_blue_led_temp_key = 0
        self.fail_blink_led_temp_key = 0
        self.fail_white_led_temp_key = 0
        self.fail_charging_test_temp_key = 0
        self.fail_sd_test_temp_key = 0
        self.fail_sg_test_temp_key = 0

        for key in sorted(self.final_analysis.keys()):
            # print"key is :      " ,key
            if self.final_analysis[key]['blue_led'] == 'fail' or self.final_analysis[key]['blue_led'] == 'Fail':
                self.blue_led_fail_cycle_counter += 1
                blue_led_temp = []

                blue_led_temp.append(self.final_analysis[key]['Date'])
                blue_led_temp.append(self.final_analysis[key]['Time'])
                self.fail_cycle_blue_led_dict[self.fail_blue_led_temp_key] = blue_led_temp
                self.fail_blue_led_temp_key += 1

            if self.final_analysis[key]['blink_led'] == 'fail' or self.final_analysis[key]['blink_led'] == 'Fail':
                self.blink_led_fail_cycle_counter += 1
                blink_led_temp = []
                blink_led_temp.append(self.final_analysis[key]['Date'])
                blink_led_temp.append(self.final_analysis[key]['Time'])
                self.fail_cycle_blink_led_dict[self.fail_blink_led_temp_key] = blink_led_temp
                self.fail_blink_led_temp_key += 1

            if self.final_analysis[key]['white_led'] == 'fail' or self.final_analysis[key]['white_led'] == 'Fail':
                self.white_led_fail_cycle_counter += 1
                white_led_temp = []
                white_led_temp.append(self.final_analysis[key]['Date'])
                white_led_temp.append(self.final_analysis[key]['Time'])
                self.fail_cycle_white_led_dict[self.fail_white_led_temp_key] = white_led_temp
                self.fail_white_led_temp_key += 1

            if self.final_analysis[key]['SD_Test'] == 'fail' or self.final_analysis[key]['SD_Test'] == 'Fail':
                self.sd_test_fail_cycle_counter += 1
                sd_temp = []
                sd_temp.append(self.final_analysis[key]['Date'])
                sd_temp.append(self.final_analysis[key]['Time'])
                self.fail_cycle_sd_test_dict[self.fail_sd_test_temp_key] = sd_temp
                self.fail_sd_test_temp_key += 1

            if self.final_analysis[key]['Charging_test'] == 'fail' or self.final_analysis[key][
                'Charging_test'] == 'Fail':
                self.charging_test_fail_cycle_counter += 1
                charging_temp = []
                charging_temp.append(self.final_analysis[key]['Date'])
                charging_temp.append(self.final_analysis[key]['Time'])
                self.fail_cycle_charging_test_dict[self.fail_charging_test_temp_key] = charging_temp
                self.fail_charging_test_temp_key += 1

            if self.final_analysis[key]['SG_Test'] == 'fail' or self.final_analysis[key]['SG_Test'] == 'Fail':
                self.sg_test_fail_cycle_counter += 1
                sg_temp = []
                sg_temp.append(self.final_analysis[key]['Date'])
                sg_temp.append(self.final_analysis[key]['Time'])
                self.fail_cycle_sg_test_dict[self.fail_sg_test_temp_key] = sg_temp
                self.fail_sg_test_temp_key += 1

            if self.final_analysis[key]['SN'] in self.all_dev_dict['dev_addr']:
                mac_index = self.all_dev_dict['dev_addr'].index(self.final_analysis[key]['SN'])
                # print mac_index
                # print key
                mac_list.append(self.final_analysis[key]['SN'])
                if self.final_analysis[key]['SN'] in self.dev_dict['dev_addr']:
                    if self.final_analysis[key]['Overall'] != "Pass":
                        self.all_dev_dict['tested_count'][mac_index] += 1
                else:
                    self.all_dev_dict['tested_count'][mac_index] += 1
                if self.all_dev_dict['tested_count'][mac_index] == 2:

                    if self.final_analysis[key]['Overall'] == "Pass":
                        # self.second_pass_counter+=1
                        self.all_dev_dict['overall_res'][mac_index] = "Pass"
                    else:
                        self.all_dev_dict['overall_res'][mac_index] = "Fail"
                    # print self.all_dev_dict['overall_res'][mac_index]
                    # print self.final_analysis[key]['mac']

                    if self.final_analysis[key]['blue_led'] == "Pass":
                        # self.second_pass_counter+=1
                        self.all_dev_dict['blue_led_fail'][mac_index] = "Pass"
                    else:
                        self.all_dev_dict['blue_led_fail'][mac_index] = "fail"

                    if self.final_analysis[key]['blink_led'] == "Pass":
                        # self.second_pass_counter+=1
                        self.all_dev_dict['blink_led_fail'][mac_index] = "Pass"
                    else:
                        self.all_dev_dict['blink_led_fail'][mac_index] = "fail"

                    if self.final_analysis[key]['white_led'] == "Pass":
                        # self.second_pass_counter+=1
                        self.all_dev_dict['white_led_fail'][mac_index] = "Pass"
                    else:
                        self.all_dev_dict['white_led_fail'][mac_index] = "fail"

                    if self.final_analysis[key]['Charging_test'] == "Pass":
                        # self.second_pass_counter+=1
                        self.all_dev_dict['charging_test_fail'][mac_index] = "Pass"
                    else:
                        self.all_dev_dict['charging_test_fail'][mac_index] = "fail"

                    if self.final_analysis[key]['SG_Test'] == "Pass":
                        # self.second_pass_counter+=1
                        self.all_dev_dict['sg_test_fail'][mac_index] = "Pass"
                    else:
                        self.all_dev_dict['sg_test_fail'][mac_index] = "fail"

                    if self.final_analysis[key]['SD_Test'] == "Pass":
                        # self.second_pass_counter+=1
                        self.all_dev_dict['sd_test_fail'][mac_index] = "Pass"
                    else:
                        self.all_dev_dict['sd_test_fail'][mac_index] = "fail"

                if self.all_dev_dict['tested_count'][mac_index] == 3:

                    # print self.final_analysis[key]['overall_res']

                    if self.final_analysis[key]['Overall'] == "Pass":

                        # self.third_pass_counter+=1
                        self.all_dev_dict['overall_res'][mac_index] = "Pass"
                    else:
                        self.all_dev_dict['overall_res'][mac_index] = "Fail"

                    if self.final_analysis[key]['blue_led'] == "Pass":
                        # self.second_pass_counter+=1
                        self.all_dev_dict['blue_led_fail'][mac_index] = "Pass"
                    else:
                        self.all_dev_dict['blue_led_fail'][mac_index] = "fail"

                    if self.final_analysis[key]['blink_led'] == "Pass":
                        # self.second_pass_counter+=1
                        self.all_dev_dict['blink_led_fail'][mac_index] = "Pass"
                    else:
                        self.all_dev_dict['blink_led_fail'][mac_index] = "fail"

                    if self.final_analysis[key]['white_led'] == "Pass":
                        # self.second_pass_counter+=1
                        self.all_dev_dict['white_led_fail'][mac_index] = "Pass"
                    else:
                        self.all_dev_dict['white_led_fail'][mac_index] = "fail"

                    if self.final_analysis[key]['Charging_test'] == "Pass":
                        # self.second_pass_counter+=1
                        self.all_dev_dict['charging_test_fail'][mac_index] = "Pass"
                    else:
                        self.all_dev_dict['charging_test_fail'][mac_index] = "fail"

                    if self.final_analysis[key]['SG_Test'] == "Pass":
                        # self.second_pass_counter+=1
                        self.all_dev_dict['sg_test_fail'][mac_index] = "Pass"
                    else:
                        self.all_dev_dict['sg_test_fail'][mac_index] = "fail"

                    if self.final_analysis[key]['SD_Test'] == "Pass":
                        # self.second_pass_counter+=1
                        self.all_dev_dict['sd_test_fail'][mac_index] = "Pass"
                    else:
                        self.all_dev_dict['sd_test_fail'][mac_index] = "fail"

                if self.all_dev_dict['tested_count'][mac_index] == 4:
                    if self.final_analysis[key]['Overall'] == "Pass":
                        # self.fourth_pass_counter+=1
                        self.all_dev_dict['overall_res'][mac_index] = "Pass"
                    else:
                        self.all_dev_dict['overall_res'][mac_index] = "Fail"
                    # print self.final_analysis[key]['mac']


                    if self.final_analysis[key]['blue_led'] == "Pass":
                        # self.second_pass_counter+=1
                        self.all_dev_dict['blue_led_fail'][mac_index] = "Pass"
                    else:
                        self.all_dev_dict['blue_led_fail'][mac_index] = "fail"

                    if self.final_analysis[key]['blink_led'] == "Pass":
                        # self.second_pass_counter+=1
                        self.all_dev_dict['blink_led_fail'][mac_index] = "Pass"
                    else:
                        self.all_dev_dict['blink_led_fail'][mac_index] = "fail"

                    if self.final_analysis[key]['white_led'] == "Pass":
                        # self.second_pass_counter+=1
                        self.all_dev_dict['white_led_fail'][mac_index] = "Pass"
                    else:
                        self.all_dev_dict['white_led_fail'][mac_index] = "fail"

                    if self.final_analysis[key]['Charging_test'] == "Pass":
                        # self.second_pass_counter+=1
                        self.all_dev_dict['charging_test_fail'][mac_index] = "Pass"
                    else:
                        self.all_dev_dict['charging_test_fail'][mac_index] = "fail"

                    if self.final_analysis[key]['SG_Test'] == "Pass":
                        # self.second_pass_counter+=1
                        self.all_dev_dict['sg_test_fail'][mac_index] = "Pass"
                    else:
                        self.all_dev_dict['sg_test_fail'][mac_index] = "fail"

                    if self.final_analysis[key]['SD_Test'] == "Pass":
                        # self.second_pass_counter+=1
                        self.all_dev_dict['sd_test_fail'][mac_index] = "Pass"
                    else:
                        self.all_dev_dict['sd_test_fail'][mac_index] = "fail"

                if self.all_dev_dict['tested_count'][mac_index] > 4:
                    # print self.final_analysis[key]['mac']
                    if self.final_analysis[key]['Overall'] == "Pass":
                        self.all_dev_dict['overall_res'][mac_index] = "Pass"
                    else:
                        self.all_dev_dict['overall_res'][mac_index] = "Fail"

                    if self.final_analysis[key]['blue_led'] == "Pass":
                        # self.second_pass_counter+=1
                        self.all_dev_dict['blue_led_fail'][mac_index] = "Pass"
                    else:
                        self.all_dev_dict['blue_led_fail'][mac_index] = "fail"

                    if self.final_analysis[key]['blink_led'] == "Pass":
                        # self.second_pass_counter+=1
                        self.all_dev_dict['blink_led_fail'][mac_index] = "Pass"
                    else:
                        self.all_dev_dict['blink_led_fail'][mac_index] = "fail"

                    if self.final_analysis[key]['white_led'] == "Pass":
                        # self.second_pass_counter+=1
                        self.all_dev_dict['white_led_fail'][mac_index] = "Pass"
                    else:
                        self.all_dev_dict['white_led_fail'][mac_index] = "fail"

                    if self.final_analysis[key]['Charging_test'] == "Pass":
                        # self.second_pass_counter+=1
                        self.all_dev_dict['charging_test_fail'][mac_index] = "Pass"
                    else:
                        self.all_dev_dict['charging_test_fail'][mac_index] = "fail"

                    if self.final_analysis[key]['SG_Test'] == "Pass":
                        # self.second_pass_counter+=1
                        self.all_dev_dict['sg_test_fail'][mac_index] = "Pass"
                    else:
                        self.all_dev_dict['sg_test_fail'][mac_index] = "fail"

                    if self.final_analysis[key]['SD_Test'] == "Pass":
                        # self.second_pass_counter+=1
                        self.all_dev_dict['sd_test_fail'][mac_index] = "Pass"
                    else:
                        self.all_dev_dict['sd_test_fail'][mac_index] = "fail"




            else:
                self.all_dev_dict['dev_addr'].append(self.final_analysis[key]['SN'])
                self.all_dev_dict['tested_count'].append(1)

                self.all_dev_dict['overall_res'].append(self.final_analysis[key]['Overall'])

                self.all_dev_dict['blue_led_fail'].append(self.final_analysis[key]['blue_led'])
                self.all_dev_dict['blink_led_fail'].append(self.final_analysis[key]['blink_led'])
                self.all_dev_dict['white_led_fail'].append(self.final_analysis[key]['white_led'])
                self.all_dev_dict['charging_test_fail'].append(self.final_analysis[key]['Charging_test'])
                self.all_dev_dict['sg_test_fail'].append(self.final_analysis[key]['SG_Test'])
                self.all_dev_dict['sd_test_fail'].append(self.final_analysis[key]['SD_Test'])

                if self.final_analysis[key]['Overall'] == "Pass":
                    t_cnt += 1
                    self.dev_dict['dev_addr'].append(self.final_analysis[key]['SN'])
                    # print self.final_analysis[key]['mac']+' : '+str(t_cnt)+' : '+str(key)
                    self.first_pass_counter += 1




        # print "ecg fail dict:   ",  self.fail_cycle_ecg_dict
        # print "spo2 fail dict:   ",  self.fail_cycle_spo2_dict
        # print "temp fail dict:   ",  self.fail_cycle_temper_dict
        # print "fuel gauge fail dict:   ",  self.fail_cycle_fuel_gauge_dict



        for i in range(len(self.all_dev_dict['dev_addr'])):
            if self.all_dev_dict['tested_count'][i] > 1:
                mac_chk_list.append(self.all_dev_dict['dev_addr'][i])



        # print mac_chk_list
        f_cnt = 0
        # for i in range(len(self.all_dev_dict['overall_res'])):
        # if self.all_dev_dict['overall_res'][i]=="Fail":
        # f_cnt+=1
        # print self.all_dev_dict['overall_res'][i]+'  :   '+str(self.all_dev_dict['tested_count'][i])

        self.failed_blue_led_fail_count = 0
        self.failed_blink_led_fail_count = 0
        self.failed_white_led_fail_count = 0
        self.failed_charging_test_fail_count = 0
        self.failed_sg_test_fail_count = 0
        self.failed_sd_test_fail_count = 0

        self.first_pass_counter = 0
        for i in range(len(self.all_dev_dict['overall_res'])):
            if self.all_dev_dict['tested_count'][i] == 1 and self.all_dev_dict['overall_res'][i] == 'Pass':
                self.first_pass_counter += 1
            if self.all_dev_dict['tested_count'][i] == 1 and (
                    self.all_dev_dict['overall_res'][i] == 'Fail' or self.all_dev_dict['overall_res'][i] == 'fail'):
                # print self.all_dev_dict['overall_res'][i]+'  :   '+str(self.all_dev_dict['tested_count'][i])
                f_cnt += 1
                if self.all_dev_dict['blue_led_fail'][i] == 'fail':
                    self.failed_blue_led_fail_count += 1
                if self.all_dev_dict['blink_led_fail'][i] == 'fail':
                    self.failed_blink_led_fail_count += 1
                if self.all_dev_dict['white_led_fail'][i] == 'fail':
                    self.failed_white_led_fail_count += 1
                if self.all_dev_dict['charging_test_fail'][i] == 'fail':
                    self.failed_charging_test_fail_count += 1
                if self.all_dev_dict['sg_test_fail'][i] == 'fail':
                    self.failed_sg_test_fail_count += 1
                if self.all_dev_dict['sd_test_fail'][i] == 'fail':
                    self.failed_sd_test_fail_count += 1

            # print self.all_dev_dict['overall_res'][i]+'  :   '+str(self.all_dev_dict['tested_count'][i])
            if self.all_dev_dict['tested_count'][i] == 2 and self.all_dev_dict['overall_res'][i] == 'Pass':
                self.second_pass_counter += 1
            if self.all_dev_dict['tested_count'][i] == 2 and (
                    self.all_dev_dict['overall_res'][i] == 'Fail' or self.all_dev_dict['overall_res'][i] == 'fail'):
                # print self.all_dev_dict['overall_res'][i]+'  :   '+str(self.all_dev_dict['tested_count'][i])
                f_cnt += 1
                if self.all_dev_dict['blue_led_fail'][i] == 'fail':
                    self.failed_blue_led_fail_count += 1
                if self.all_dev_dict['blink_led_fail'][i] == 'fail':
                    self.failed_blink_led_fail_count += 1
                if self.all_dev_dict['white_led_fail'][i] == 'fail':
                    self.failed_white_led_fail_count += 1
                if self.all_dev_dict['charging_test_fail'][i] == 'fail':
                    self.failed_charging_test_fail_count += 1
                if self.all_dev_dict['sg_test_fail'][i] == 'fail':
                    self.failed_sg_test_fail_count += 1
                if self.all_dev_dict['sd_test_fail'][i] == 'fail':
                    self.failed_sd_test_fail_count += 1

            if self.all_dev_dict['tested_count'][i] == 3 and self.all_dev_dict['overall_res'][i] == 'Pass':
                self.third_pass_counter += 1
            if self.all_dev_dict['tested_count'][i] == 3 and (
                    self.all_dev_dict['overall_res'][i] == 'Fail' or self.all_dev_dict['overall_res'][i] == 'fail'):
                # print self.all_dev_dict['overall_res'][i]+'  :   '+str(self.all_dev_dict['tested_count'][i])
                f_cnt += 1
                if self.all_dev_dict['blue_led_fail'][i] == 'fail':
                    self.failed_blue_led_fail_count += 1
                if self.all_dev_dict['blink_led_fail'][i] == 'fail':
                    self.failed_blink_led_fail_count += 1
                if self.all_dev_dict['white_led_fail'][i] == 'fail':
                    self.failed_white_led_fail_count += 1
                if self.all_dev_dict['charging_test_fail'][i] == 'fail':
                    self.failed_charging_test_fail_count += 1
                if self.all_dev_dict['sg_test_fail'][i] == 'fail':
                    self.failed_sg_test_fail_count += 1
                if self.all_dev_dict['sd_test_fail'][i] == 'fail':
                    self.failed_sd_test_fail_count += 1

            if self.all_dev_dict['tested_count'][i] == 4 and self.all_dev_dict['overall_res'][i] == "Pass":
                self.fourth_pass_counter += 1
            if self.all_dev_dict['tested_count'][i] == 4 and (
                    self.all_dev_dict['overall_res'][i] == 'Fail' or self.all_dev_dict['overall_res'][i] == 'fail'):
                # print self.all_dev_dict['overall_res'][i]+'  :   '+str(self.all_dev_dict['tested_count'][i])
                f_cnt += 1
                if self.all_dev_dict['blue_led_fail'][i] == 'fail':
                    self.failed_blue_led_fail_count += 1
                if self.all_dev_dict['blink_led_fail'][i] == 'fail':
                    self.failed_blink_led_fail_count += 1
                if self.all_dev_dict['white_led_fail'][i] == 'fail':
                    self.failed_white_led_fail_count += 1
                if self.all_dev_dict['charging_test_fail'][i] == 'fail':
                    self.failed_charging_test_fail_count += 1
                if self.all_dev_dict['sg_test_fail'][i] == 'fail':
                    self.failed_sg_test_fail_count += 1
                if self.all_dev_dict['sd_test_fail'][i] == 'fail':
                    self.failed_sd_test_fail_count += 1

            if self.all_dev_dict['tested_count'][i] > 4 and self.all_dev_dict['overall_res'][i] == 'Pass':
                self.other_pass_counter += 1
            if self.all_dev_dict['tested_count'][i] > 4 and (
                    self.all_dev_dict['overall_res'][i] == 'Fail' or self.all_dev_dict['overall_res'][i] == 'fail'):
                # print self.all_dev_dict['overall_res'][i]+'  :   '+str(self.all_dev_dict['tested_count'][i])
                f_cnt += 1
                if self.all_dev_dict['blue_led_fail'][i] == 'fail':
                    self.failed_blue_led_fail_count += 1
                if self.all_dev_dict['blink_led_fail'][i] == 'fail':
                    self.failed_blink_led_fail_count += 1
                if self.all_dev_dict['white_led_fail'][i] == 'fail':
                    self.failed_white_led_fail_count += 1
                if self.all_dev_dict['charging_test_fail'][i] == 'fail':
                    self.failed_charging_test_fail_count += 1
                if self.all_dev_dict['sg_test_fail'][i] == 'fail':
                    self.failed_sg_test_fail_count += 1
                if self.all_dev_dict['sd_test_fail'][i] == 'fail':
                    self.failed_sd_test_fail_count += 1


        # print f_cnt

        self.fail_devices_counter = f_cnt

        self.blue_led_fail_cycle.SetLabel(str(self.blue_led_fail_cycle_counter))
        self.blink_led_fail_cycle.SetLabel(str(self.blink_led_fail_cycle_counter))
        self.white_led_fail_cycle.SetLabel(str(self.white_led_fail_cycle_counter))
        self.charging_test_fail_cycle.SetLabel(str(self.charging_test_fail_cycle_counter))
        self.sg_test_fail_cycle.SetLabel(str(self.sg_test_fail_cycle_counter))
        self.sd_test_fail_cycle.SetLabel(str(self.sd_test_fail_cycle_counter))

        self.total_fail_cycle.SetLabel(
            str(self.blue_led_fail_cycle_counter + self.blink_led_fail_cycle_counter + self.white_led_fail_cycle_counter
                + self.charging_test_fail_cycle_counter + self.sg_test_fail_cycle_counter + self.sd_test_fail_cycle_counter))

        self.total_unique_device_tested.SetLabel(str(len(self.all_dev_dict['dev_addr'])))
        self.total_pass.SetLabel(str(
            self.first_pass_counter + self.second_pass_counter + self.third_pass_counter + self.fourth_pass_counter + self.other_pass_counter))

        self.retest_devices.SetLabel(str(len(mac_chk_list)))
        self.first_pass.SetLabel(str(self.first_pass_counter))
        self.second_pass.SetLabel(str(self.second_pass_counter))
        self.third_pass.SetLabel(str(self.third_pass_counter))
        self.fourth_pass.SetLabel(str(self.fourth_pass_counter))
        self.other_pass.SetLabel(str(self.other_pass_counter))
        self.fail_devices.SetLabel(str(self.fail_devices_counter))

        self.blue_led_fail_in_failed_cycle.SetLabel(str(self.failed_blue_led_fail_count))
        self.blink_led_fail_in_failed_cycle.SetLabel(str(self.failed_blink_led_fail_count))
        self.white_led_fail_in_failed_cycle.SetLabel(str(self.failed_white_led_fail_count))
        self.charging_test_fail_in_failed_cycle.SetLabel(str(self.failed_charging_test_fail_count))
        self.sg_test_fail_in_failed_cycle.SetLabel(str(self.failed_sg_test_fail_count))
        self.sd_test_fail_in_failed_cycle.SetLabel(str(self.failed_sd_test_fail_count))

        self.total_failed_cycle.SetLabel(str(
            self.failed_blue_led_fail_count + self.failed_blink_led_fail_count + self.failed_white_led_fail_count + self.failed_charging_test_fail_count
            + self.failed_sg_test_fail_count + self.failed_sd_test_fail_count))

    def gen_all_res(self, filename):
        global pcba_row_header
        fi = open(filename, 'rb')
        data = fi.read()
        # print data
        fi.close()
        fo = open(filename, 'wb')
        fo.write(data.replace('\x00', ''))
        fo.close()
        f = open(filename, 'rt')
        reader = csv.reader(f)
        first_row = True

        self.index_dict = {}
        self.dates = []

        for field in pcba_row_header:
            self.index_dict[field] = -2

        # print self.index_dict
        self.final = {}

        self.count = 0
        for row in reader:
            # print row

            if first_row:
                first_row = False

                for i in range(len(row)):

                    for field in self.index_dict.keys():
                        # print field+' : '+row[i]
                        if field == row[i]:
                            self.index_dict[field] = i


                # print self.index_dict

                temp_list = []
                for key in self.index_dict.keys():
                    temp_list.append(self.index_dict[key])

                max_index = max(temp_list)
            # print max_index
            else:

                if len(row) < max_index:  # corrupted data, ignore
                    continue

                if row[self.index_dict['Date']].find(' ') == -1:  # corrupted data , ignore
                    continue
                res = {}
                for res_key in pcba_row_header:
                    # print res_key

                    res[res_key] = row[self.index_dict[res_key]]
                # print res_key+':'+res[res_key]
                self.final[self.count] = res
                self.count += 1
                if row[self.index_dict['Date']] not in self.dates:
                    self.dates.append((row[self.index_dict['Date']]))
                # print self.dates
        self.dates = sort_dates(self.dates)
        # print self.dates
        if len(self.dates) == 0:
            self.start_date_combo_box.SetItems(['No Data'])
            self.end_date_combo_box.SetItems(['No Data'])
            self.analyze_btn.Enable(False)
        else:

            self.start_date_combo_box.SetItems(self.dates)
            self.end_date_combo_box.SetItems(self.dates)
            self.start_date_combo_box.SetValue(self.dates[0])
            self.end_date_combo_box.SetValue(self.dates[-1])
            # print self.start_date_combo_box.GetValue()
            # print self.end_date_combo_box.GetValue()
            self.analyze_btn.Enable(True)

    def load_file_btn_click(self, event):
        global pcba_first_load_click
        dlg = wx.FileDialog(self, message="Open a csv File...", defaultDir=os.getcwd(),
                            defaultFile="", style=wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            # User has selected something, get the path, set the window's title to the path
            filename = dlg.GetPath()
            self.fpath = filename

        self.reverse_csv(self.fpath)
        self.gen_all_res(self.fpath)
        if pcba_first_load_click:
            pcba_first_load_click = False
        else:

            self.blue_led_fail_cycle.SetLabel(str(0))
            self.blink_led_fail_cycle.SetLabel(str(0))
            self.white_led_fail_cycle.SetLabel(str(0))
            self.sd_test_fail_cycle.SetLabel(str(0))
            self.sg_test_fail_cycle.SetLabel(str(0))
            self.charging_test_fail_cycle.SetLabel(str(0))

            self.total_fail_cycle.SetLabel(str(0))
            self.total_unique_device_tested.SetLabel(str(0))
            self.retest_devices.SetLabel(str(0))
            self.first_pass.SetLabel(str(0))
            self.second_pass.SetLabel(str(0))
            self.third_pass.SetLabel(str(0))
            self.fourth_pass.SetLabel(str(0))
            self.other_pass.SetLabel(str(0))
            self.fail_devices.SetLabel(str(0))


class Sync_win(wx.Panel):
    def __init__(self, parent, style=wx.SIMPLE_BORDER, size=(800, 800), clearSigInt=True):

        self.dates = []


        wx.Panel.__init__(self, parent)
        self.Total_Analysis = wx.StaticBox(self, -1, 'Total Analysis', size=(800, 50), pos=(80, 40))
        self.Total_Analysis_Sizer = wx.StaticBoxSizer(self.Total_Analysis, wx.VERTICAL)

        # Total Analysis
        self.AnalysisSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.Total_Pass_Analysis = wx.StaticBox(self, -1, 'Pass Analysis', size=(800, 240), pos=(80, 90))
        self.Total_Pass_Analysis_Sizer = wx.StaticBoxSizer(self.Total_Pass_Analysis, wx.VERTICAL)

        # Pass Analysis
        self.PassAnalysisSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.analyze_btn = wx.Button(self, label="Analyze", pos=(650, 10))
        self.analyze_btn.Enable(False)
        self.Bind(wx.EVT_BUTTON, self.analyze_btn_click, self.analyze_btn)

        self.load_file_btn = wx.Button(self, label="Load File", pos=(20, 10))
        self.load_file_btn.Enable(True)
        self.Bind(wx.EVT_BUTTON, self.load_file_btn_click, self.load_file_btn)

        wx.StaticText(self, -1, 'Start Date : ', (130, 10))
        self.start_date_combo_box = wx.ComboBox(self, -1, '-', pos=(220, 10), size=(120, -1), choices=self.dates,
                                                style=wx.CB_READONLY)

        wx.StaticText(self, -1, 'End Date : ', (370, 10))
        self.end_date_combo_box = wx.ComboBox(self, -1, '-', pos=(450, 10), size=(120, -1), choices=self.dates,
                                              style=wx.CB_READONLY)

        wx.StaticText(self, -1, 'Total unique devices tested: ', (100, 60))
        self.total_unique_device_tested = wx.StaticText(self, -1, '', (400,60))

        wx.StaticText(self, -1, 'Total pass: ', (500, 60))
        self.total_pass = wx.StaticText(self, -1, '', (600, 60))

        wx.StaticText(self, -1, 'First Pass : ', (100, 120))
        self.first_pass = wx.StaticText(self, -1, '', (400, 120))

        wx.StaticText(self, -1, 'Second Pass : ', (100, 150))
        self.second_pass = wx.StaticText(self, -1, '', (400, 150))

        wx.StaticText(self, -1, 'Third Pass : ', (100, 180))
        self.third_pass = wx.StaticText(self, -1, '', (400, 180))

        wx.StaticText(self, -1, 'Fourth Pass : ', (100, 210))
        self.fourth_pass = wx.StaticText(self, -1, '', (400, 210))

        wx.StaticText(self, -1, 'Other Pass : ', (100, 240))
        self.other_pass = wx.StaticText(self, -1, '', (400, 240))

        wx.StaticText(self, -1, 'Fail Device : ', (700, 60))
        self.fail_devices = wx.StaticText(self, -1, '', (800, 60))

        wx.StaticText(self, -1, 'Retested Devices : ', (100, 270))
        self.retest_devices = wx.StaticText(self, -1, '', (400, 270))

        self.AnalysisSizer.Add(self.total_unique_device_tested, 0, wx.ALL | wx.CENTER, 2)
        self.AnalysisSizer.Add(self.total_pass, 0, wx.ALL | wx.CENTER, 2)
        self.AnalysisSizer.Add(self.fail_devices, 0, wx.ALL | wx.CENTER, 2)

        self.Total_Analysis_Sizer.Add(self.AnalysisSizer, 0, wx.ALL | wx.CENTER, 5)


    def analyze_btn_click(self, event):

        start_date = self.start_date_combo_box.GetValue()
        end_date = self.end_date_combo_box.GetValue()

        if is_greater(start_date, end_date):
            Info(self, "Please select valid start date and end date", "Invalid Selection", new=1)
            self.start_date_combo_box.SetValue(self.last_start_date)
            self.end_date_combo_box.SetValue(self.last_end_date)

        self.final_analysis = {}  # store all data according extracted date

        self.temp_date_list = []  # store all date from start date to end date

        if is_equal(start_date, end_date):
            for k in range(self.count):
                # print self.count
                if is_equal(start_date, self.final[k]['date']):
                    self.final_analysis[k] = self.final[k]

        # print final_analysis
        else:
            if is_greater(end_date, start_date):
                start_index = self.dates.index(start_date)
                end_index = self.dates.index(end_date)
            # print start_index
            # print end_index
            self.temp_date_list = self.dates[start_index:end_index + 1]
            for m in range(len(self.temp_date_list)):

                for k in range(self.count):
                    if is_equal(self.temp_date_list[m], self.final[k]['date']):
                        self.final_analysis[k] = self.final[k]

        # print self.final_analysis
        self.all_dev_dict = {'dev_addr': [], 'tested_count': [], 'overall_res': []}
        self.dev_dict = {'dev_addr': []}

        self.retest_counter = 0
        self.first_pass_counter = 0
        self.second_pass_counter = 0
        self.third_pass_counter = 0
        self.fourth_pass_counter = 0
        self.other_pass_counter = 0
        self.fail_devices_counter = 0

        chk_cnt = 0
        t_cnt = 0
        mac_list = []
        mac_chk_list = []

        for key in sorted(self.final_analysis.keys()):
            # print"key is :      " ,key

            if self.final_analysis[key]['sn'] in self.all_dev_dict['dev_addr']:
                mac_index = self.all_dev_dict['dev_addr'].index(self.final_analysis[key]['sn'])
                # print mac_index
                # print key
                mac_list.append(self.final_analysis[key]['sn'])
                if self.final_analysis[key]['sn'] in self.dev_dict['dev_addr']:
                    if self.final_analysis[key]['overall'] != "Pass":
                        self.all_dev_dict['tested_count'][mac_index] += 1
                else:
                    self.all_dev_dict['tested_count'][mac_index] += 1
                if self.all_dev_dict['tested_count'][mac_index] == 2:

                    if self.final_analysis[key]['overall'] == "Pass":
                        # self.second_pass_counter+=1
                        self.all_dev_dict['overall_res'][mac_index] = "Pass"
                    else:
                        self.all_dev_dict['overall_res'][mac_index] = "Fail"
                    # print self.all_dev_dict['overall_res'][mac_index]
                    # print self.final_analysis[key]['mac']
                if self.all_dev_dict['tested_count'][mac_index] == 3:

                    # print self.final_analysis[key]['overall_res']

                    if self.final_analysis[key]['overall'] == "Pass":

                        # self.third_pass_counter+=1
                        self.all_dev_dict['overall_res'][mac_index] = "Pass"
                    else:
                        self.all_dev_dict['overall_res'][mac_index] = "Fail"

                if self.all_dev_dict['tested_count'][mac_index] == 4:
                    if self.final_analysis[key]['overall'] == "Pass":
                        # self.fourth_pass_counter+=1
                        self.all_dev_dict['overall_res'][mac_index] = "Pass"
                    else:
                        self.all_dev_dict['overall_res'][mac_index] = "Fail"
                    # print self.final_analysis[key]['mac']
                if self.all_dev_dict['tested_count'][mac_index] > 4:
                    # print self.final_analysis[key]['mac']
                    if self.final_analysis[key]['overall'] == "Pass":
                        self.all_dev_dict['overall_res'][mac_index] = "Pass"
                    else:
                        self.all_dev_dict['overall_res'][mac_index] = "Fail"


            else:
                self.all_dev_dict['dev_addr'].append(self.final_analysis[key]['sn'])
                self.all_dev_dict['tested_count'].append(1)

                self.all_dev_dict['overall_res'].append(self.final_analysis[key]['overall'])

                if self.final_analysis[key]['overall'] == "Pass":
                    t_cnt += 1
                    self.dev_dict['dev_addr'].append(self.final_analysis[key]['sn'])
                    # print self.final_analysis[key]['mac']+' : '+str(t_cnt)+' : '+str(key)
                    self.first_pass_counter += 1




        # print "ecg fail dict:   ",  self.fail_cycle_ecg_dict
        # print "spo2 fail dict:   ",  self.fail_cycle_spo2_dict
        # print "temp fail dict:   ",  self.fail_cycle_temper_dict
        # print "fuel gauge fail dict:   ",  self.fail_cycle_fuel_gauge_dict



        for i in range(len(self.all_dev_dict['dev_addr'])):
            if self.all_dev_dict['tested_count'][i] > 1:
                mac_chk_list.append(self.all_dev_dict['dev_addr'][i])



        # print mac_chk_list
        f_cnt = 0
        # for i in range(len(self.all_dev_dict['overall_res'])):
        # if self.all_dev_dict['overall_res'][i]=="Fail":
        # f_cnt+=1
        # print self.all_dev_dict['overall_res'][i]+'  :   '+str(self.all_dev_dict['tested_count'][i])


        self.first_pass_counter = 0

        for i in range(len(self.all_dev_dict['overall_res'])):
            if self.all_dev_dict['tested_count'][i] == 1 and self.all_dev_dict['overall_res'][i] == 'Pass':
                self.first_pass_counter += 1
            if self.all_dev_dict['tested_count'][i] == 1 and self.all_dev_dict['overall_res'][i] == 'Fail':
                # print self.all_dev_dict['overall_res'][i]+'  :   '+str(self.all_dev_dict['tested_count'][i])
                f_cnt += 1
            # print self.all_dev_dict['overall_res'][i]+'  :   '+str(self.all_dev_dict['tested_count'][i])
            if self.all_dev_dict['tested_count'][i] == 2 and self.all_dev_dict['overall_res'][i] == 'Pass':
                self.second_pass_counter += 1
            if self.all_dev_dict['tested_count'][i] == 2 and self.all_dev_dict['overall_res'][i] == 'Fail':
                # print self.all_dev_dict['overall_res'][i]+'  :   '+str(self.all_dev_dict['tested_count'][i])
                f_cnt += 1
            if self.all_dev_dict['tested_count'][i] == 3 and self.all_dev_dict['overall_res'][i] == 'Pass':
                self.third_pass_counter += 1
            if self.all_dev_dict['tested_count'][i] == 3 and self.all_dev_dict['overall_res'][i] == 'Fail':
                # print self.all_dev_dict['overall_res'][i]+'  :   '+str(self.all_dev_dict['tested_count'][i])
                f_cnt += 1

            if self.all_dev_dict['tested_count'][i] == 4 and self.all_dev_dict['overall_res'][i] == "Pass":
                self.fourth_pass_counter += 1
            if self.all_dev_dict['tested_count'][i] == 4 and self.all_dev_dict['overall_res'][i] == 'Fail':
                # print self.all_dev_dict['overall_res'][i]+'  :   '+str(self.all_dev_dict['tested_count'][i])
                f_cnt += 1
            if self.all_dev_dict['tested_count'][i] > 4 and self.all_dev_dict['overall_res'][i] == 'Pass':
                self.other_pass_counter += 1
            if self.all_dev_dict['tested_count'][i] > 4 and self.all_dev_dict['overall_res'][i] == 'Fail':
                # print self.all_dev_dict['overall_res'][i]+'  :   '+str(self.all_dev_dict['tested_count'][i])
                f_cnt += 1


        # print f_cnt

        self.fail_devices_counter = f_cnt

        self.total_unique_device_tested.SetLabel(str(len(self.all_dev_dict['dev_addr'])))
        self.total_pass.SetLabel(str(
            self.first_pass_counter + self.second_pass_counter + self.third_pass_counter + self.fourth_pass_counter + self.other_pass_counter))
        self.retest_devices.SetLabel(str(len(mac_chk_list)))
        self.first_pass.SetLabel(str(self.first_pass_counter))
        self.second_pass.SetLabel(str(self.second_pass_counter))
        self.third_pass.SetLabel(str(self.third_pass_counter))
        self.fourth_pass.SetLabel(str(self.fourth_pass_counter))
        self.other_pass.SetLabel(str(self.other_pass_counter))
        self.fail_devices.SetLabel(str(self.fail_devices_counter))

    def gen_all_res(self, filename):
        global charger_row_header
        fi = open(filename, 'rb')
        data = fi.read()
        # print data
        fi.close()
        fo = open(filename, 'wb')
        fo.write(data.replace('\x00', ''))
        fo.close()
        f = open(filename, 'rt')
        reader = csv.reader(f)
        first_row = True

        self.index_dict = {}
        self.dates = []

        for field in charger_row_header:
            self.index_dict[field] = -2

        # print self.index_dict
        self.final = {}

        self.count = 0
        for row in reader:
            # print row

            if first_row:
                first_row = False

                for i in range(len(row)):

                    for field in self.index_dict.keys():
                        # print field+' : '+row[i]
                        if field == row[i]:
                            self.index_dict[field] = i


                # print self.index_dict

                temp_list = []
                for key in self.index_dict.keys():
                    temp_list.append(self.index_dict[key])

                max_index = max(temp_list)
            # print max_index
            else:

                if len(row) < max_index:  # corrupted data, ignore
                    continue

                if row[self.index_dict['date']].find(' ') == -1:  # corrupted data , ignore
                    continue
                res = {}
                for res_key in charger_row_header:
                    # print res_key

                    res[res_key] = row[self.index_dict[res_key]]
                # print res_key+':'+res[res_key]
                self.final[self.count] = res
                self.count += 1
                if row[self.index_dict['date']] not in self.dates:
                    self.dates.append((row[self.index_dict['date']]))
                # print self.dates
        self.dates = sort_dates(self.dates)
        if len(self.dates) == 0:
            self.start_date_combo_box.SetItems(['No Data'])
            self.end_date_combo_box.SetItems(['No Data'])
            self.analyze_btn.Enable(False)
        else:

            self.start_date_combo_box.SetItems(self.dates)
            self.end_date_combo_box.SetItems(self.dates)
            self.start_date_combo_box.SetValue(self.dates[0])
            self.end_date_combo_box.SetValue(self.dates[-1])
            # print self.start_date_combo_box.GetValue()
            # print self.end_date_combo_box.GetValue()
            self.analyze_btn.Enable(True)

    def reverse_csv(self, filename):
        global charger_csv_list
        global charger_row_header
        fi = open(filename, 'rb')
        data = fi.read()
        # print data
        fi.close()
        fo = open(filename, 'wb')
        fo.write(data.replace('\x00', ''))
        fo.close()
        f = open(filename, 'rt')
        reader = csv.reader(f)
        csv_first_row = True
        charger_csv_list = []

        for row in reader:
            # print row

            if csv_first_row:
                csv_first_row = False
                charger_row_header = row
            # print row_header
            else:
                charger_csv_list.append(row)

        '''charger_csv_list=charger_csv_list[::-1]
        #print 'csv list::'
        print charger_csv_list
        f.close()

        out=open(filename,"w")#opening csv in append mode
        output=csv.writer(out)#getting object of csv writer
        output.writerow(charger_row_header)#writing row into csv file
        for row_append in charger_csv_list:
            output.writerow(row_append)

        out.close()'''

    def load_file_btn_click(self, event):
        global charger_first_load_click
        dlg = wx.FileDialog(self, message="Open a csv File...", defaultDir=os.getcwd(),
                            defaultFile="", style=wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            # User has selected something, get the path, set the window's title to the path
            filename = dlg.GetPath()
            self.fpath = filename
        self.reverse_csv(self.fpath)
        self.gen_all_res(self.fpath)
        if charger_first_load_click:
            charger_first_load_click = False
        else:
            self.total_unique_device_tested.SetLabel(str(0))
            self.retest_devices.SetLabel(str(0))
            self.first_pass.SetLabel(str(0))
            self.second_pass.SetLabel(str(0))
            self.third_pass.SetLabel(str(0))
            self.fourth_pass.SetLabel(str(0))
            self.other_pass.SetLabel(str(0))
            self.fail_devices.SetLabel(str(0))


class Download_win(wx.Panel):
    def __init__(self, parent, style=wx.SIMPLE_BORDER, size=(500, 500), clearSigInt=True):
        # frame = wx.Frame(None,title="Download",pos=findScreenCenter(450,450), size=(700,450))
        self.dates = []

        wx.Panel.__init__(self, parent)

        self.download_btn = wx.Button(self, ID_DOWNLOAD, "Download File", pos=(330, 200))
        self.download_btn.Enable(True)
        self.Bind(wx.EVT_BUTTON, self.download_btn_click, id=ID_DOWNLOAD)
        self.start_btn = wx.Button(self, label="Start Date", pos=(100, 80))
        self.Bind(wx.EVT_BUTTON, self.start_btn_click, self.start_btn, id=ID_START_DATE)
        self.end_btn = wx.Button(self, label="End Date", pos=(100, 140))
        self.Bind(wx.EVT_BUTTON, self.end_btn_click, self.end_btn, id=ID_END_DATE)

        wx.StaticText(self, -1, ' Select Software', (100, 30))
        project_Options = ['System', 'Pcba', 'charger']
        self.project_Combo_Box = wx.ComboBox(self, -1, project_Options[0], pos=(250, 30), choices=project_Options,
                                             style=wx.CB_READONLY)

        self.selected_start_date = wx.StaticText(self, -1, '', (430, 80))
        self.selected_end_date = wx.StaticText(self, -1, '', (430, 140))

        wx.StaticText(self, -1, 'Total Downloaded Data : ', (330, 250))
        self.download_percent = wx.StaticText(self, -1, '', (530, 250))
        # Set up event handler for any worker thread results
        EVT_RESULT(self, self.OnResult)

        EVT_START_DATE(self, self.OnStartDateSelected)
        EVT_END_DATE(self, self.OnEndDateSelected)


        # And indicate we don't have a worker thread yet
        self.worker = None

    def OnStartDateSelected(self, event):
        """Show Result status."""
        # print event.data
        if event.data is None:

            dlg = wx.MessageDialog(self, "Date Not Selected ", 'Info', wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()

        else:
            # print "event data is"+str(event.data)
            self.selected_start_date.SetLabel(event.data)

    def OnEndDateSelected(self, event):
        """Show Result status."""
        # print event.data
        if event.data is None:

            dlg = wx.MessageDialog(self, "Date Not Selected ", 'Info', wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()

        else:
            # print "event data is"+str(event.data)
            self.selected_end_date.SetLabel(event.data)

    def start_btn_click(self, event):
        chgdep = MyCalendar(self, 'DatePicker')
        chgdep.ShowModal()
        chgdep.Destroy()

    def end_btn_click(self, event):
        chgdep = MyCalendar1(self, 'DatePicker')
        chgdep.ShowModal()
        chgdep.Destroy()

    # split date in day month and year
    def download_split_date(self, date):
        splitted = date.split('/')
        # print splitted
        year = splitted[2]
        month = splitted[0]
        day = splitted[1]
        return day, month, year

    # check whether date1 is greater than date2
    def download_is_greater(self, date1, date2):
        # print date1,date2

        day1, month1, year1 = self.download_split_date(date1)
        day2, month2, year2 = self.download_split_date(date2)

        if int(year1) < int(year2) or int(month1) < int(month2) or int(day1) < int(day2):
            # print "returning false y "
            return False
        elif int(year1) > int(year2) or int(month1) > int(month2) or int(day1) > int(day2):
            # print "returning false y "
            return True

    # check whether date1 is equal to date2
    def download_is_equal(self, date1, date2):
        # print date1,date2

        day1, month1, year1 = self.download_split_date(date1)
        day2, month2, year2 = self.download_split_date(date2)

        if int(year1) == int(year2) and int(month1) == int(month2) and int(day1) == int(day2):
            # print "returning false y "
            return True
        else:
            return False

    # for dialog box
    def download_Info(parent, message, caption='INFO', new=0):
        if new == 0:
            return
        dlg = wx.MessageDialog(parent, message, caption, wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

    def download_btn_click(self, evt):
        self.download_btn.Enable(False)
        global start_date_picked
        global end_date_picked
        self.selected_start_date.SetLabel(start_date_picked)
        self.selected_end_date.SetLabel(end_date_picked)
        download_start_date = self.selected_start_date.GetLabel()
        download_end_date = self.selected_end_date.GetLabel()

        self.project_to_download = self.project_Combo_Box.GetValue()
        if download_start_date == '' or download_end_date == '':
            dlg = wx.MessageDialog(self, "Please select start and end date For Downloading", 'Info',
                                   wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.download_btn.Enable(True)
        else:

            if self.download_is_greater(download_start_date, download_end_date):
                dlg = wx.MessageDialog(self, "Please Select valid start and end Date", 'Info',
                                       wx.OK | wx.ICON_INFORMATION)
                dlg.ShowModal()
                dlg.Destroy()
                self.download_btn.Enable(True)

            else:
                self.start_date_list = str(download_start_date).split('/')
                self.end_date_list = str(download_end_date).split('/')
                # Trigger the worker thread unless it's already busy
                if not self.worker:
                    # self.status.SetLabel('Starting computation')
                    # print "download clicked"
                    self.worker = WorkerThread(self, self.start_date_list, self.end_date_list, self.project_to_download)

                # self.download_data(start_date_list,end_date_list)

    def OnResult(self, event):
        """Show Result status."""
        if event.data is None:
            # Thread aborted (using our convention of None return)
            # self.status.SetLabel('Computation aborted')
            dlg = wx.MessageDialog(self, "Data not Found ,Please select Date again ", 'Info',
                                   wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.download_btn.Enable(True)

        else:
            if event.data is -1:
                dlg = wx.MessageDialog(self, "Please check Internet Connection", 'Info', wx.OK | wx.ICON_INFORMATION)
                dlg.ShowModal()
                dlg.Destroy()
                self.download_btn.Enable(True)
            else:
                # Process results here
                # self.status.SetLabel('Computation Result: %s' % event.data)
                # print 'progressing'+str(event.data)+str(event.data2)
                self.download_percent.SetLabel(str(int(event.data)))
                if event.data2 == True:
                    self.download_btn.Enable(True)
                    download_start_date_url = str(
                        str(self.start_date_list[2])[:4] + '-' + str(self.start_date_list[0]) + '-' + str(
                            self.start_date_list[1]))
                    download_end_date_url = str(
                        str(self.end_date_list[2])[:4] + '-' + str(self.end_date_list[0]) + '-' + str(
                            self.end_date_list[1]))

                    dlg = wx.MessageDialog(self, "File name is " + "data_" + str(
                        self.project_to_download) + "_" + download_start_date_url + " to " + download_end_date_url + ".csv",
                                           'Download Completed', wx.OK | wx.ICON_INFORMATION)
                    dlg.ShowModal()
                    dlg.Destroy()


        # In either event, the worker is done
        self.worker = None


class SaveFileAs(wx.Dialog):
    def __init__(self, parent, mytitle):
        wx.Dialog.__init__(self, parent, wx.ID_ANY, mytitle)
        self.parent = parent
        self.Save_As = wx.StaticText(self, -1, "Save As")
        self.Save_File = wx.TextCtrl(self, name="Save As")
        self.Save_btn = wx.Button(self, wx.ID_OK, "Save")
        self.cancel_btn = wx.Button(self, wx.ID_CANCEL, "Cancel")
        self.Bind(wx.EVT_BUTTON, self.onCancel_btn_click, self.cancel_btn)
        self.Bind(wx.EVT_BUTTON, self.onSave_btn_click, self.Save_btn)

    def onSave_btn_click(self):
        self.file_name = self.Save_File.GetValue()

    def onCancel_btn_click(self):
        pass


class MyCalendar(wx.Dialog):
    """create a simple dialog window with a calendar display"""

    def __init__(self, parent, mytitle):
        wx.Dialog.__init__(self, parent, wx.ID_ANY, mytitle)
        # use a box sizer to position controls vertically
        vbox = wx.BoxSizer(wx.VERTICAL)
        self.parent = parent
        # wx.DateTime_Now() sets calendar to current date
        self.calendar = cal.CalendarCtrl(self, wx.ID_ANY, wx.DateTime_Now(), style=cal.CAL_SEQUENTIAL_MONTH_SELECTION)
        vbox.Add(self.calendar, 0, wx.EXPAND | wx.ALL, border=20)
        # click on day
        self.calendar.Bind(cal.EVT_CALENDAR_DAY, self.onCalSelected)
        # change month
        self.calendar.Bind(cal.EVT_CALENDAR_MONTH, self.onCalSelected)
        # change year
        self.calendar.Bind(cal.EVT_CALENDAR_YEAR, self.onCalSelected)
        self.startlabel = wx.StaticText(self, wx.ID_ANY, 'click on a day')
        vbox.Add(self.startlabel, 0, wx.EXPAND | wx.ALL, border=20)
        button = wx.Button(self, wx.ID_ANY, 'Exit')
        vbox.Add(button, 0, wx.ALL | wx.ALIGN_CENTER, border=20)
        self.Bind(wx.EVT_BUTTON, self.onQuit, button)

        self.SetSizerAndFit(vbox)
        self.Show(True)
        self.Centre()

    def onCalSelected(self, event):
        global start_date_picked


        # date = event.GetDate()
        date = self.calendar.GetDate()
        day = date.GetDay()
        # for some strange reason month starts with zero
        month = date.GetMonth() + 1
        # year is yyyy format
        year = date.GetYear()
        # format the date string to your needs
        ds = "%02d/%02d/%d \n" % (month, day, year)
        start_date_picked = ds

        self.startlabel.SetLabel(ds)
        wx.PostEvent(self.parent, StartDateEvent(start_date_picked))

    def onQuit(self, event):
        print "something"

        self.Destroy()


class MyCalendar1(wx.Dialog):
    """create a simple dialog window with a calendar display"""

    def __init__(self, parent, mytitle):
        wx.Dialog.__init__(self, parent, wx.ID_ANY, mytitle)
        # use a box sizer to position controls vertically
        vbox = wx.BoxSizer(wx.VERTICAL)
        self.parent = parent
        # wx.DateTime_Now() sets calendar to current date
        self.calendar = cal.CalendarCtrl(self, wx.ID_ANY, wx.DateTime_Now(), style=cal.CAL_SEQUENTIAL_MONTH_SELECTION)
        vbox.Add(self.calendar, 0, wx.EXPAND | wx.ALL, border=20)
        # click on day
        self.calendar.Bind(cal.EVT_CALENDAR_DAY, self.onCalSelected)
        # change month
        self.calendar.Bind(cal.EVT_CALENDAR_MONTH, self.onCalSelected)
        # change year
        self.calendar.Bind(cal.EVT_CALENDAR_YEAR, self.onCalSelected)
        self.endlabel = wx.StaticText(self, wx.ID_ANY, 'click on a day')
        vbox.Add(self.endlabel, 0, wx.EXPAND | wx.ALL, border=20)
        button = wx.Button(self, wx.ID_ANY, 'Exit')
        vbox.Add(button, 0, wx.ALL | wx.ALIGN_CENTER, border=20)
        self.Bind(wx.EVT_BUTTON, self.onQuit, button)
        self.SetSizerAndFit(vbox)
        self.Show(True)
        self.Centre()

    def onCalSelected(self, event):
        global end_date_picked


        # date = event.GetDate()
        date = self.calendar.GetDate()
        day = date.GetDay()
        # for some strange reason month starts with zero
        month = date.GetMonth() + 1
        # year is yyyy format
        year = date.GetYear()
        # format the date string to your needs
        ds = "%02d/%02d/%d \n" % (month, day, year)
        end_date_picked = ds

        self.endlabel.SetLabel(ds)
        wx.PostEvent(self.parent, EndDateEvent(end_date_picked))

    def onQuit(self, event):
        self.Destroy()


class AnalysisPanel(wx.Panel):
    def __init__(self, parent, style=wx.SIMPLE_BORDER, size=(500, 500), clearSigInt=True):
        self.fpath = ''

        self.enable = True

        self.last_start_date = 'None'
        self.last_end_date = 'None'

        self.index_dict = {}

        wx.Panel.__init__(self, parent)

        self.Total_Analysis = wx.StaticBox(self, -1, 'Total Analysis', size=(800, 50), pos=(80, 40))
        self.Total_Analysis_Sizer = wx.StaticBoxSizer(self.Total_Analysis, wx.VERTICAL)

        # Total Analysis
        self.AnalysisSizer = wx.BoxSizer(wx.HORIZONTAL)


        self.Total_Pass_Analysis = wx.StaticBox(self, -1, 'Pass Analysis', size=(800, 240), pos=(80, 90))
        self.Total_Pass_Analysis_Sizer = wx.StaticBoxSizer(self.Total_Pass_Analysis, wx.VERTICAL)

        # Pass Analysis
        self.PassAnalysisSizer = wx.BoxSizer(wx.HORIZONTAL)



        self.Overall_Fail_Analysis = wx.StaticBox(self, -1, 'Overall Fail Cycles', size=(400, 170), pos=(80, 340))
        self.Overall_Fail_Analysis_Sizer = wx.StaticBoxSizer(self.Overall_Fail_Analysis, wx.VERTICAL)

        # Overall Fail Cycles
        self.OverallFailAnalysisSizer = wx.BoxSizer(wx.HORIZONTAL)



        self.Failed_Analysis = wx.StaticBox(self, -1, 'Failed Device Fail Cycles ', size=(400, 170), pos=(480, 340))
        self.Failed_Analysis_Sizer = wx.StaticBoxSizer(self.Failed_Analysis, wx.VERTICAL)

        # Failed Device Fail Cycles
        self.FailedAnalysisSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.dates = []

        self.data_diff = ["Local", "Main"]
        self.analyze_btn = wx.Button(self, label="Analyze", pos=(750, 10))
        self.analyze_btn.Enable(False)
        wx.StaticText(self, -1, 'Data:', (580, 10))
        self.data_combo_box = wx.ComboBox(self, -1, '-', pos=(620, 10), size=(120, -1), choices=self.data_diff,
                                          style=wx.CB_READONLY)
        self.Bind(wx.EVT_BUTTON, self.analyze_btn_click, self.analyze_btn)

        self.load_file_btn = wx.Button(self, label="Load File", pos=(20, 10))
        self.load_file_btn.Enable(True)

        self.Bind(wx.EVT_BUTTON, self.load_file_btn_click, self.load_file_btn)
        wx.StaticText(self, -1, 'Start Date : ', (130, 10))
        self.start_date_combo_box = wx.ComboBox(self, -1, '-', pos=(220, 10), size=(120, -1), choices=self.dates,
                                                style=wx.CB_READONLY)
        wx.StaticText(self, -1, 'End Date : ', (370, 10))
        self.end_date_combo_box = wx.ComboBox(self, -1, '-', pos=(450, 10), size=(120, -1), choices=self.dates,
                                              style=wx.CB_READONLY)

        wx.StaticText(self, -1, 'Total unique devices tested: ', (100, 60))
        self.total_unique_device_tested = wx.StaticText(self, -1, '', (400, 60))

        wx.StaticText(self, -1, 'Total pass: ', (500, 60))
        self.total_pass = wx.StaticText(self, -1, '', (600, 60))

        wx.StaticText(self, -1, 'First Pass : ', (100, 120))
        self.first_pass = wx.StaticText(self, -1, '', (400, 120))

        wx.StaticText(self, -1, 'Second Pass : ', (100, 150))
        self.second_pass = wx.StaticText(self, -1, '', (400, 150))

        wx.StaticText(self, -1, 'Third Pass : ', (100, 180))
        self.third_pass = wx.StaticText(self, -1, '', (400, 180))

        wx.StaticText(self, -1, 'Fourth Pass : ', (100, 210))
        self.fourth_pass = wx.StaticText(self, -1, '', (400, 210))

        wx.StaticText(self, -1, 'Other Pass : ', (100, 240))
        self.other_pass = wx.StaticText(self, -1, '', (400, 240))

        wx.StaticText(self, -1, 'Fail Device : ', (700, 60))
        self.fail_devices = wx.StaticText(self, -1, '', (800, 60))

        wx.StaticText(self, -1, 'Fail Cycle : ', (500, 360))
        self.total_failed_cycle = wx.StaticText(self, -1, '', (800, 360))

        wx.StaticText(self, -1, 'ecg : ', (530, 390))
        self.ecg_fail_in_failed_cycle = wx.StaticText(self, -1, '', (800, 390))

        wx.StaticText(self, -1, 'spo2 : ', (530, 420))
        self.spo2_fail_in_failed_cycle = wx.StaticText(self, -1, '', (800, 420))

        wx.StaticText(self, -1, 'temperature : ', (530, 450))
        self.temp_fail_in_failed_cycle = wx.StaticText(self, -1, '', (800, 450))

        wx.StaticText(self, -1, 'fuel gauge : ', (530, 480))
        self.fuel_gauge_fail_in_failed_cycle = wx.StaticText(self, -1, '', (800, 480))

        wx.StaticText(self, -1, 'Battery level-[0 %] : ', (100, 270))
        self.battery_level_0 = wx.StaticText(self, -1, '', (400, 270))

        wx.StaticText(self, -1, 'Retested Devices : ', (100, 300))
        self.retest_devices = wx.StaticText(self, -1, '', (400, 300))

        wx.StaticText(self, -1, 'Fail Cycle : ', (100, 360))
        self.total_fail_cycle = wx.StaticText(self, -1, '', (400, 360))

        wx.StaticText(self, -1, 'ecg : ', (130, 390))
        self.ecg_fail_cycle = wx.StaticText(self, -1, '', (400, 390))

        wx.StaticText(self, -1, 'spo2 : ', (130, 420))
        self.spo2_fail_cycle = wx.StaticText(self, -1, '', (400, 420))

        wx.StaticText(self, -1, 'temperature : ', (130, 450))
        self.temp_fail_cycle = wx.StaticText(self, -1, '', (400, 450))

        wx.StaticText(self, -1, 'fuel gauge : ', (130, 480))
        self.fuel_gauge_fail_cycle = wx.StaticText(self, -1, '', (400, 480))

        self.AnalysisSizer.Add(self.total_unique_device_tested, 0, wx.ALL | wx.CENTER, 2)
        self.AnalysisSizer.Add(self.total_pass, 0, wx.ALL | wx.CENTER, 2)
        self.AnalysisSizer.Add(self.fail_devices, 0, wx.ALL | wx.CENTER, 2)

        self.Total_Analysis_Sizer.Add(self.AnalysisSizer, 0, wx.ALL | wx.CENTER, 5)

        # self.fpath = './logs/temp_logs.csv'
        # self.new_filepath='./new_data.csv'
        global fpath
        fpath = self.fpath

    def download_btn_click(self, evet):

        app = wx.App(0)

        frame = wx.Frame(None, title="Download File", pos=findScreenCenter(500, 500), size=(750, 500))
        panel = Download_win(frame)
        frame.Show()

        app.MainLoop()

    def charger_pcba_btn_click(self, evet):

        app = wx.App(0)

        frame = wx.Frame(None, title="Charger Analysis", pos=findScreenCenter(500, 500), size=(900, 500))
        panel = Sync_win(frame)
        frame.Show()

        app.MainLoop()

    def pcba_test_click(self, evet):

        app = wx.App(0)

        frame = wx.Frame(None, title="Pcba Analysis", pos=findScreenCenter(500, 500), size=(900, 600))
        panel = Pcba_win(frame)
        frame.Show()

        app.MainLoop()

    def reverse_csv(self, filename):
        global csv_list
        global row_header
        fi = open(filename, 'rb')
        data = fi.read()
        # print data
        fi.close()
        fo = open(filename, 'wb')
        fo.write(data.replace('\x00', ''))
        fo.close()
        f = open(filename, 'rt')
        reader = csv.reader(f)
        csv_first_row = True
        csv_list = []

        for row in reader:
            # print row

            if csv_first_row:
                csv_first_row = False
                row_header = row
            # print row_header
            else:
                csv_list.append(row)

        '''csv_list=csv_list[::-1]
        #print 'csv list::'
        #print csv_list
        f.close()

        out=open(filename,"w")#opening csv in append mode
        output=csv.writer(out)#getting object of csv writer
        output.writerow(row_header)#writing row into csv file
        for row_append in csv_list:
            output.writerow(row_append)

        out.close()'''

    def analyze_btn_click(self, event):

        start_date = self.start_date_combo_box.GetValue()
        end_date = self.end_date_combo_box.GetValue()
        data_diff = self.data_combo_box.GetValue()

        if is_greater(start_date, end_date):
            Info(self, "Please select valid start date and end date", "Invalid Selection", new=1)
            self.start_date_combo_box.SetValue(self.last_start_date)
            self.end_date_combo_box.SetValue(self.last_end_date)

        self.final_analysis = {}  # store all data according extracted date
        self.final_analysis_local = {}  # store all data according extracted date and data(local)
        self.final_analysis_main = {}  # store all data according extracted date and data(main)

        self.temp_date_list = []  # store all date from start date to end date

        if is_equal(start_date, end_date):
            for k in range(self.count):
                # print self.count
                if is_equal(start_date, self.final[k]['date']):
                    if self.final[k]['firmware_imgB_version'] == '---':
                        self.final_analysis_local[k] = self.final[k]
                    else:
                        self.final_analysis_main[k] = self.final[k]
            if data_diff == 'Local':
                self.final_analysis = self.final_analysis_local
            else:
                self.final_analysis = self.final_analysis_main

        # print final_analysis
        else:
            if is_greater(end_date, start_date):
                start_index = self.dates.index(start_date)
                end_index = self.dates.index(end_date)
            # print start_index
            # print end_index
            self.temp_date_list = self.dates[start_index:end_index + 1]
            for m in range(len(self.temp_date_list)):

                for k in range(self.count):
                    if is_equal(self.temp_date_list[m], self.final[k]['date']):
                        if self.final[k]['firmware_imgB_version'] == '---':
                            self.final_analysis_local[k] = self.final[k]
                        else:
                            self.final_analysis_main[k] = self.final[k]

            if data_diff == 'Local':
                self.final_analysis = self.final_analysis_local
            else:
                self.final_analysis = self.final_analysis_main

        # print self.final_analysis
        self.all_dev_dict = {'dev_addr': [], 'tested_count': [], 'overall_res': [], 'ecg_fail': [], 'spo2_fail': [],
                             'temp_fail': [], 'fuel_gauge_fail': []}
        self.dev_dict = {'dev_addr': []}

        self.ecg_fail_cycle_counter = 0
        self.spo2_fail_cycle_counter = 0
        self.temp_fail_cycle_counter = 0
        self.fuel_gauge_fail_cycle_counter = 0
        self.retest_counter = 0
        self.first_pass_counter = 0
        self.second_pass_counter = 0
        self.third_pass_counter = 0
        self.fourth_pass_counter = 0
        self.other_pass_counter = 0
        self.fail_devices_counter = 0

        self.battery_0_counter = 0
        chk_cnt = 0
        t_cnt = 0
        mac_list = []
        mac_chk_list = []
        self.fail_cycle_ecg_dict = {}
        self.fail_cycle_spo2_dict = {}
        self.fail_cycle_temper_dict = {}
        self.fail_cycle_fuel_gauge_dict = {}
        self.fail_ecg_temp_key = 0
        self.fail_spo2_temp_key = 0
        self.fail_temper_temp_key = 0
        self.fail_fuel_gauge_temp_key = 0

        for key in sorted(self.final_analysis.keys()):
            # print"key is :      " ,key
            if self.final_analysis[key]['ecg'] == 'fail' or self.final_analysis[key]['ecg'] == 'Fail':
                self.ecg_fail_cycle_counter += 1
                ecg_temp = []

                ecg_temp.append(self.final_analysis[key]['date'])
                ecg_temp.append(self.final_analysis[key]['time'])
                self.fail_cycle_ecg_dict[self.fail_ecg_temp_key] = ecg_temp
                self.fail_ecg_temp_key += 1

            if self.final_analysis[key]['spo2'] == 'fail' or self.final_analysis[key]['spo2'] == 'Fail':
                self.spo2_fail_cycle_counter += 1
                spo2_temp = []
                spo2_temp.append(self.final_analysis[key]['date'])
                spo2_temp.append(self.final_analysis[key]['time'])
                self.fail_cycle_spo2_dict[self.fail_spo2_temp_key] = spo2_temp
                self.fail_spo2_temp_key += 1
            if self.final_analysis[key]['temp'] == 'fail' or self.final_analysis[key]['temp'] == 'Fail':
                self.temp_fail_cycle_counter += 1
                temper_temp = []
                temper_temp.append(self.final_analysis[key]['date'])
                temper_temp.append(self.final_analysis[key]['time'])
                self.fail_cycle_temper_dict[self.fail_temper_temp_key] = temper_temp
                self.fail_temper_temp_key += 1
            if self.final_analysis[key]['fuelgauge'] == 'fail' or self.final_analysis[key]['fuelgauge'] == 'Fail':
                self.fuel_gauge_fail_cycle_counter += 1
                fuel_temp = []
                fuel_temp.append(self.final_analysis[key]['date'])
                fuel_temp.append(self.final_analysis[key]['time'])
                self.fail_cycle_fuel_gauge_dict[self.fail_fuel_gauge_temp_key] = fuel_temp
                self.fail_fuel_gauge_temp_key += 1
            if self.final_analysis[key]['mac'] in self.all_dev_dict['dev_addr']:
                mac_index = self.all_dev_dict['dev_addr'].index(self.final_analysis[key]['mac'])
                # print mac_index
                # print key
                mac_list.append(self.final_analysis[key]['mac'])
                if self.final_analysis[key]['mac'] in self.dev_dict['dev_addr']:
                    if self.final_analysis[key]['overall_res'] != "Pass":
                        self.all_dev_dict['tested_count'][mac_index] += 1
                else:
                    self.all_dev_dict['tested_count'][mac_index] += 1
                if self.all_dev_dict['tested_count'][mac_index] == 2:

                    if self.final_analysis[key]['overall_res'] == "Pass":
                        # self.second_pass_counter+=1
                        self.all_dev_dict['overall_res'][mac_index] = "Pass"
                    else:
                        self.all_dev_dict['overall_res'][mac_index] = "Fail"
                    # print self.all_dev_dict['overall_res'][mac_index]
                    # print self.final_analysis[key]['mac']

                    if self.final_analysis[key]['ecg'] == "pass":
                        # self.second_pass_counter+=1
                        self.all_dev_dict['ecg_fail'][mac_index] = "pass"
                    else:
                        self.all_dev_dict['ecg_fail'][mac_index] = "fail"

                    if self.final_analysis[key]['spo2'] == "pass":
                        # self.second_pass_counter+=1
                        self.all_dev_dict['spo2_fail'][mac_index] = "pass"
                    else:
                        self.all_dev_dict['spo2_fail'][mac_index] = "fail"

                    if self.final_analysis[key]['temp'] == "pass":
                        # self.second_pass_counter+=1
                        self.all_dev_dict['temp_fail'][mac_index] = "pass"
                    else:
                        self.all_dev_dict['temp_fail'][mac_index] = "fail"

                    if self.final_analysis[key]['fuelgauge'] == "pass":
                        # self.second_pass_counter+=1
                        self.all_dev_dict['fuel_gauge_fail'][mac_index] = "pass"
                    else:
                        self.all_dev_dict['fuel_gauge_fail'][mac_index] = "fail"

                if self.all_dev_dict['tested_count'][mac_index] == 3:

                    # print self.final_analysis[key]['overall_res']

                    if self.final_analysis[key]['overall_res'] == "Pass":

                        # self.third_pass_counter+=1
                        self.all_dev_dict['overall_res'][mac_index] = "Pass"
                    else:
                        self.all_dev_dict['overall_res'][mac_index] = "Fail"

                    if self.final_analysis[key]['ecg'] == "pass":
                        # self.second_pass_counter+=1
                        self.all_dev_dict['ecg_fail'][mac_index] = "pass"
                    else:
                        self.all_dev_dict['ecg_fail'][mac_index] = "fail"

                    if self.final_analysis[key]['spo2'] == "pass":
                        # self.second_pass_counter+=1
                        self.all_dev_dict['spo2_fail'][mac_index] = "pass"
                    else:
                        self.all_dev_dict['spo2_fail'][mac_index] = "fail"

                    if self.final_analysis[key]['temp'] == "pass":
                        # self.second_pass_counter+=1
                        self.all_dev_dict['temp_fail'][mac_index] = "pass"
                    else:
                        self.all_dev_dict['temp_fail'][mac_index] = "fail"

                    if self.final_analysis[key]['fuelgauge'] == "pass":
                        # self.second_pass_counter+=1
                        self.all_dev_dict['fuel_gauge_fail'][mac_index] = "pass"
                    else:
                        self.all_dev_dict['fuel_gauge_fail'][mac_index] = "fail"

                if self.all_dev_dict['tested_count'][mac_index] == 4:
                    if self.final_analysis[key]['overall_res'] == "Pass":
                        # self.fourth_pass_counter+=1
                        self.all_dev_dict['overall_res'][mac_index] = "Pass"
                    else:
                        self.all_dev_dict['overall_res'][mac_index] = "Fail"
                    # print self.final_analysis[key]['mac']


                    if self.final_analysis[key]['ecg'] == "pass":
                        # self.second_pass_counter+=1
                        self.all_dev_dict['ecg_fail'][mac_index] = "pass"
                    else:
                        self.all_dev_dict['ecg_fail'][mac_index] = "fail"

                    if self.final_analysis[key]['spo2'] == "pass":
                        # self.second_pass_counter+=1
                        self.all_dev_dict['spo2_fail'][mac_index] = "pass"
                    else:
                        self.all_dev_dict['spo2_fail'][mac_index] = "fail"

                    if self.final_analysis[key]['temp'] == "pass":
                        # self.second_pass_counter+=1
                        self.all_dev_dict['temp_fail'][mac_index] = "pass"
                    else:
                        self.all_dev_dict['temp_fail'][mac_index] = "fail"

                    if self.final_analysis[key]['fuelgauge'] == "pass":
                        # self.second_pass_counter+=1
                        self.all_dev_dict['fuel_gauge_fail'][mac_index] = "pass"
                    else:
                        self.all_dev_dict['fuel_gauge_fail'][mac_index] = "fail"

                if self.all_dev_dict['tested_count'][mac_index] > 4:
                    # print self.final_analysis[key]['mac']
                    if self.final_analysis[key]['overall_res'] == "Pass":
                        self.all_dev_dict['overall_res'][mac_index] = "Pass"
                    else:
                        self.all_dev_dict['overall_res'][mac_index] = "Fail"

                    if self.final_analysis[key]['ecg'] == "pass":
                        # self.second_pass_counter+=1
                        self.all_dev_dict['ecg_fail'][mac_index] = "pass"
                    else:
                        self.all_dev_dict['ecg_fail'][mac_index] = "fail"

                    if self.final_analysis[key]['spo2'] == "pass":
                        # self.second_pass_counter+=1
                        self.all_dev_dict['spo2_fail'][mac_index] = "pass"
                    else:
                        self.all_dev_dict['spo2_fail'][mac_index] = "fail"

                    if self.final_analysis[key]['temp'] == "pass":
                        # self.second_pass_counter+=1
                        self.all_dev_dict['temp_fail'][mac_index] = "pass"
                    else:
                        self.all_dev_dict['temp_fail'][mac_index] = "fail"

                    if self.final_analysis[key]['fuelgauge'] == "pass":
                        # self.second_pass_counter+=1
                        self.all_dev_dict['fuel_gauge_fail'][mac_index] = "pass"
                    else:
                        self.all_dev_dict['fuel_gauge_fail'][mac_index] = "fail"

                if self.final_analysis[key]['battery_per'] == "0":
                    self.battery_0_counter += 1
            else:
                self.all_dev_dict['dev_addr'].append(self.final_analysis[key]['mac'])
                self.all_dev_dict['tested_count'].append(1)

                self.all_dev_dict['overall_res'].append(self.final_analysis[key]['overall_res'])
                self.all_dev_dict['ecg_fail'].append(self.final_analysis[key]['ecg'])
                self.all_dev_dict['spo2_fail'].append(self.final_analysis[key]['spo2'])
                self.all_dev_dict['temp_fail'].append(self.final_analysis[key]['temp'])
                self.all_dev_dict['fuel_gauge_fail'].append(self.final_analysis[key]['fuelgauge'])

                if self.final_analysis[key]['overall_res'] == "Pass":
                    t_cnt += 1
                    self.dev_dict['dev_addr'].append(self.final_analysis[key]['mac'])
                    # print self.final_analysis[key]['mac']+' : '+str(t_cnt)+' : '+str(key)
                    self.first_pass_counter += 1

                if self.final_analysis[key]['battery_per'] == "0":
                    self.battery_0_counter += 1

        # print "ecg fail dict:   ",  self.fail_cycle_ecg_dict
        # print "spo2 fail dict:   ",  self.fail_cycle_spo2_dict
        # print "temp fail dict:   ",  self.fail_cycle_temper_dict
        # print "fuel gauge fail dict:   ",  self.fail_cycle_fuel_gauge_dict



        for i in range(len(self.all_dev_dict['dev_addr'])):
            if self.all_dev_dict['tested_count'][i] > 1:
                mac_chk_list.append(self.all_dev_dict['dev_addr'][i])



        # print mac_chk_list
        f_cnt = 0
        # for i in range(len(self.all_dev_dict['overall_res'])):
        # if self.all_dev_dict['overall_res'][i]=="Fail":
        # f_cnt+=1
        # print self.all_dev_dict['overall_res'][i]+'  :   '+str(self.all_dev_dict['tested_count'][i])

        self.failed_ecg_fail_count = 0
        self.failed_spo2_fail_count = 0
        self.failed_temp_fail_count = 0
        self.failed_fuelgauge_fail_count = 0

        self.first_pass_counter = 0
        for i in range(len(self.all_dev_dict['overall_res'])):
            if self.all_dev_dict['tested_count'][i] == 1 and self.all_dev_dict['overall_res'][i] == 'Pass':
                self.first_pass_counter += 1
            if self.all_dev_dict['tested_count'][i] == 1 and self.all_dev_dict['overall_res'][i] == 'Fail':
                # print self.all_dev_dict['overall_res'][i]+'  :   '+str(self.all_dev_dict['tested_count'][i])
                f_cnt += 1
                if self.all_dev_dict['ecg_fail'][i] == 'fail':
                    self.failed_ecg_fail_count += 1
                if self.all_dev_dict['spo2_fail'][i] == 'fail':
                    self.failed_spo2_fail_count += 1
                if self.all_dev_dict['temp_fail'][i] == 'fail':
                    self.failed_temp_fail_count += 1
                if self.all_dev_dict['fuel_gauge_fail'][i] == 'fail':
                    self.failed_fuelgauge_fail_count += 1

            # print self.all_dev_dict['overall_res'][i]+'  :   '+str(self.all_dev_dict['tested_count'][i])
            if self.all_dev_dict['tested_count'][i] == 2 and self.all_dev_dict['overall_res'][i] == 'Pass':
                self.second_pass_counter += 1
            if self.all_dev_dict['tested_count'][i] == 2 and self.all_dev_dict['overall_res'][i] == 'Fail':
                # print self.all_dev_dict['overall_res'][i]+'  :   '+str(self.all_dev_dict['tested_count'][i])
                f_cnt += 1
                if self.all_dev_dict['ecg_fail'][i] == 'fail':
                    self.failed_ecg_fail_count += 1
                if self.all_dev_dict['spo2_fail'][i] == 'fail':
                    self.failed_spo2_fail_count += 1
                if self.all_dev_dict['temp_fail'][i] == 'fail':
                    self.failed_temp_fail_count += 1
                if self.all_dev_dict['fuel_gauge_fail'][i] == 'fail':
                    self.failed_fuelgauge_fail_count += 1

            if self.all_dev_dict['tested_count'][i] == 3 and self.all_dev_dict['overall_res'][i] == 'Pass':
                self.third_pass_counter += 1
            if self.all_dev_dict['tested_count'][i] == 3 and self.all_dev_dict['overall_res'][i] == 'Fail':
                # print self.all_dev_dict['overall_res'][i]+'  :   '+str(self.all_dev_dict['tested_count'][i])
                f_cnt += 1
                if self.all_dev_dict['ecg_fail'][i] == 'fail':
                    self.failed_ecg_fail_count += 1
                if self.all_dev_dict['spo2_fail'][i] == 'fail':
                    self.failed_spo2_fail_count += 1
                if self.all_dev_dict['temp_fail'][i] == 'fail':
                    self.failed_temp_fail_count += 1
                if self.all_dev_dict['fuel_gauge_fail'][i] == 'fail':
                    self.failed_fuelgauge_fail_count += 1

            if self.all_dev_dict['tested_count'][i] == 4 and self.all_dev_dict['overall_res'][i] == "Pass":
                self.fourth_pass_counter += 1
            if self.all_dev_dict['tested_count'][i] == 4 and self.all_dev_dict['overall_res'][i] == 'Fail':
                # print self.all_dev_dict['overall_res'][i]+'  :   '+str(self.all_dev_dict['tested_count'][i])
                f_cnt += 1
                if self.all_dev_dict['ecg_fail'][i] == 'fail':
                    self.failed_ecg_fail_count += 1
                if self.all_dev_dict['spo2_fail'][i] == 'fail':
                    self.failed_spo2_fail_count += 1
                if self.all_dev_dict['temp_fail'][i] == 'fail':
                    self.failed_temp_fail_count += 1
                if self.all_dev_dict['fuel_gauge_fail'][i] == 'fail':
                    self.failed_fuelgauge_fail_count += 1

            if self.all_dev_dict['tested_count'][i] > 4 and self.all_dev_dict['overall_res'][i] == 'Pass':
                self.other_pass_counter += 1
            if self.all_dev_dict['tested_count'][i] > 4 and self.all_dev_dict['overall_res'][i] == 'Fail':
                # print self.all_dev_dict['overall_res'][i]+'  :   '+str(self.all_dev_dict['tested_count'][i])
                f_cnt += 1
                if self.all_dev_dict['ecg_fail'][i] == 'fail':
                    self.failed_ecg_fail_count += 1
                if self.all_dev_dict['spo2_fail'][i] == 'fail':
                    self.failed_spo2_fail_count += 1
                if self.all_dev_dict['temp_fail'][i] == 'fail':
                    self.failed_temp_fail_count += 1
                if self.all_dev_dict['fuel_gauge_fail'][i] == 'fail':
                    self.failed_fuelgauge_fail_count += 1


        # print f_cnt

        self.fail_devices_counter = f_cnt

        self.ecg_fail_cycle.SetLabel(str(self.ecg_fail_cycle_counter))
        self.spo2_fail_cycle.SetLabel(str(self.spo2_fail_cycle_counter))
        self.temp_fail_cycle.SetLabel(str(self.temp_fail_cycle_counter))
        self.fuel_gauge_fail_cycle.SetLabel(str(self.fuel_gauge_fail_cycle_counter))
        self.total_fail_cycle.SetLabel(str(
            self.ecg_fail_cycle_counter + self.spo2_fail_cycle_counter + self.temp_fail_cycle_counter + self.fuel_gauge_fail_cycle_counter))
        self.total_unique_device_tested.SetLabel(str(len(self.all_dev_dict['dev_addr'])))
        self.total_pass.SetLabel(str(
            self.first_pass_counter + self.second_pass_counter + self.third_pass_counter + self.fourth_pass_counter + self.other_pass_counter))
        self.retest_devices.SetLabel(str(len(mac_chk_list)))
        self.first_pass.SetLabel(str(self.first_pass_counter))
        self.second_pass.SetLabel(str(self.second_pass_counter))
        self.third_pass.SetLabel(str(self.third_pass_counter))
        self.fourth_pass.SetLabel(str(self.fourth_pass_counter))
        self.other_pass.SetLabel(str(self.other_pass_counter))
        self.fail_devices.SetLabel(str(self.fail_devices_counter))
        self.battery_level_0.SetLabel(str(self.battery_0_counter))

        self.ecg_fail_in_failed_cycle.SetLabel(str(self.failed_ecg_fail_count))
        self.spo2_fail_in_failed_cycle.SetLabel(str(self.failed_spo2_fail_count))
        self.temp_fail_in_failed_cycle.SetLabel(str(self.failed_temp_fail_count))
        self.fuel_gauge_fail_in_failed_cycle.SetLabel(str(self.failed_fuelgauge_fail_count))
        self.total_failed_cycle.SetLabel(str(
            self.failed_ecg_fail_count + self.failed_spo2_fail_count + self.failed_temp_fail_count + self.failed_fuelgauge_fail_count))

    def gen_all_res(self, filename):
        global row_header
        fi = open(filename, 'rb')
        data = fi.read()
        # print data
        fi.close()
        fo = open(filename, 'wb')
        fo.write(data.replace('\x00', ''))
        fo.close()
        f = open(filename, 'rt')
        reader = csv.reader(f)
        first_row = True

        self.index_dict = {}
        self.dates = []

        for field in row_header:
            self.index_dict[field] = -2

        # print self.index_dict
        self.final = {}

        self.count = 0
        for row in reader:
            # print row

            if first_row:
                first_row = False

                for i in range(len(row)):

                    for field in self.index_dict.keys():
                        # print field+' : '+row[i]
                        if field == row[i]:
                            self.index_dict[field] = i


                # print self.index_dict

                temp_list = []
                for key in self.index_dict.keys():
                    temp_list.append(self.index_dict[key])

                max_index = max(temp_list)
            # print max_index
            else:

                if len(row) < max_index:  # corrupted data, ignore
                    continue

                if row[self.index_dict['date']].find(' ') == -1:  # corrupted data , ignore
                    continue
                res = {}
                for res_key in row_header:
                    # print res_key

                    res[res_key] = row[self.index_dict[res_key]]
                # print res_key+':'+res[res_key]
                self.final[self.count] = res
                self.count += 1
                if row[self.index_dict['date']] not in self.dates:
                    self.dates.append((row[self.index_dict['date']]))
                # print self.dates
        self.dates = sort_dates(self.dates)
        if len(self.dates) == 0:
            self.start_date_combo_box.SetItems(['No Data'])
            self.end_date_combo_box.SetItems(['No Data'])
            self.analyze_btn.Enable(False)
        else:

            self.start_date_combo_box.SetItems(self.dates)
            self.end_date_combo_box.SetItems(self.dates)
            self.start_date_combo_box.SetValue(self.dates[0])
            self.end_date_combo_box.SetValue(self.dates[-1])
            # print self.start_date_combo_box.GetValue()
            # print self.end_date_combo_box.GetValue()
            self.analyze_btn.Enable(True)

    def load_file_btn_click(self, event):
        global first_load_click
        dlg = wx.FileDialog(self, message="Open a csv File...", defaultDir=os.getcwd(),
                            defaultFile="", style=wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            # User has selected something, get the path, set the window's title to the path
            filename = dlg.GetPath()
            self.fpath = filename
        self.reverse_csv(self.fpath)
        self.gen_all_res(self.fpath)
        if first_load_click:
            first_load_click = False
        else:

            self.ecg_fail_cycle.SetLabel(str(0))
            self.spo2_fail_cycle.SetLabel(str(0))
            self.temp_fail_cycle.SetLabel(str(0))
            self.fuel_gauge_fail_cycle.SetLabel(str(0))
            self.total_fail_cycle.SetLabel(str(0))
            self.total_unique_device_tested.SetLabel(str(0))
            self.retest_devices.SetLabel(str(0))
            self.first_pass.SetLabel(str(0))
            self.second_pass.SetLabel(str(0))
            self.third_pass.SetLabel(str(0))
            self.fourth_pass.SetLabel(str(0))
            self.other_pass.SetLabel(str(0))
            self.fail_devices.SetLabel(str(0))

            self.battery_level_0.SetLabel(str(0))


def findScreenCenter(APPWIDTH, APPHEIGHT):
    w = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_X)
    h = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_Y)
    w = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_X)
    h = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_Y)

    # Centre of the screen
    x = w / 2
    y = h / 2

    # Minus application offset
    x -= (APPWIDTH / 2)
    y -= (APPHEIGHT / 2)

    pos = (x, y)
    return pos


def sort_dates(date_list):
    print "calling sort dates"
    for i in range(len(date_list)):
        for j in range(len(date_list)):
            if not is_greater(date_list[i], date_list[j]):
                temp = date_list[i]
                date_list[i] = date_list[j]
                date_list[j] = temp
    return date_list


def main():
    app = wx.App(0)

    frame = wx.Frame(None, title="System Test Analysis", pos=findScreenCenter(500, 500), size=(900, 600))
    menuBar = wx.MenuBar()
    # Download
    menu1 = wx.Menu()
    dwnld = menu1.Append(wx.NewId(), "Download", "Download")

    charger_pcba_test = menu1.Append(wx.NewId(), "Charger", "Charger")
    pcba_test = menu1.Append(wx.NewId(), "Pcba Level", "Pcba Level")

    menuBar.Append(menu1, "File")

    frame.SetMenuBar(menuBar)
    panel = AnalysisPanel(frame)
    frame.Bind(wx.EVT_MENU, panel.download_btn_click, dwnld)
    frame.Bind(wx.EVT_MENU, panel.charger_pcba_btn_click, charger_pcba_test)
    frame.Bind(wx.EVT_MENU, panel.pcba_test_click, pcba_test)

    # panel.BackgroundColour="Light Blue"
    frame.Show()

    if not os.path.isdir("./System"):
        os.mkdir("./System")

    if not os.path.isdir("./Pcba"):
        os.mkdir("./Pcba")

    if not os.path.isdir("./Charger"):
        os.mkdir("./Charger")

    app.MainLoop()


main()
