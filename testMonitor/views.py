from django.shortcuts import render
from django.http import HttpResponse, JsonResponse

import random
import radar
import datetime
import string
from typing import List, Dict
import os
import pandas as pd


def test(request):
    return HttpResponse()


def formatData(rawData):
    PROPERTIES = ['Project Name', 'Repo Name', 'Success Rate',
                  'Total', 'Succeeded', 'Failed', 'Unresolvable']
    res = []
    data = [[row[0], row[1], round(float(row[3]) / (int(row[2]) if row[2] != '0' else 1), 2), int(
        row[2]), int(row[3]), int(row[4]), int(row[5])] for row in rawData]
    data.sort(key=lambda row: row[3], reverse=True)
    for i in range(len(data)):
        res.append({PROPERTIES[j]: data[i][j] for j in range(len(PROPERTIES))})
    return res


def getProjectStatistics(request):
    os.chdir('/usr/local/projects/django/testCenter/testMonitor/oerv_obsdata')
    os.system('git pull')

    with open('./obsData/projectStatistics.txt') as f:
        rawData = list(map(lambda line: line[:-1].split('  '), f.readlines()))
    return JsonResponse({'data': formatData(rawData)})


def getDiffs(request):
    # change path for both os and file operation
    os.chdir('/usr/local/projects/django/testCenter/testMonitor/oerv_obsdata')

    def update(date_after: str = '2022-06-08') -> None:
        # get lists of commit dates and commit ids
        os.system('git pull')
        os.system(
            'git log --pretty=format:"%cd,%H,%s" --date=format:"%Y%m%d" --after="{}" > ./commitlog.txt'.format(date_after))
        dates: List[str] = []
        commitID: List[str] = []
        with open('./commitlog.txt') as f:
            for line in f.readlines():
                temp = line[:-1].split(',')
                if temp[0] not in dates:
                    dates.append(temp[0])
                    commitID.append(temp[1])
        df = pd.DataFrame({'date': dates, 'id': commitID})
        df.to_csv('./date_id.csv', index=False)

    def getDiffs(date1: str = '20220726', date2: str = '20220807'):

        df = pd.read_csv('./date_id.csv', index_col='date')
        # change dtype of index
        df.index = df.index.map(str)
        id1, id2 = df.loc[date1, 'id'], df.loc[date2, 'id']
        os.system('git diff {} {} ./obsData/projectStatistics.txt > {}'.format(id1, id2, './diff.txt'))
        deleted: List = []
        added: List = []
        with open('./diff.txt') as f:
            lines = f.readlines()
            # start from 6th line
            for i in range(6, len(lines)):
                if lines[i][0] == '-':
                    deleted.append(lines[i][1:-1].split('  ')) # strip off + / - and new line character
                elif lines[i][0] == '+':
                    added.append(lines[i][1:-1].split('  '))
        added = formatData(added)
        deleted = formatData(deleted) 

        diffs: Dict[str, List] = {'add': [], 'delete': [], 'former': [], 'latter': []}
        # given two sequence, find the matching items.
        res = []
        mark = 0
        for i in range(len(deleted)):
            indicator = True
            for j in range(mark, len(added)):
                if deleted[i]['Project Name'] == added[j]['Project Name'] and deleted[i]['Repo Name'] == added[j]['Repo Name']:
                    diffs['former'].append(deleted[i])
                    diffs['latter'].append(added[j])
                    for k in range(mark, j): diffs['add'].append(added[k])
                    mark = j + 1
                    indicator = False
                    break
            if indicator: diffs['delete'].append(deleted[i])
        
        # item['condition'] means type when data type is 'add' for 'delete', otherwise means index in their own type sequence
        latterCount = 0
        for key, values in diffs.items():
            for value in values:
                if key == 'former': value['addition'] = -1
                elif key == 'latter':
                    value['addition'] = latterCount
                    latterCount += 1
                else: value['addition'] = key 
                res.append(value)
        return res 

    update()
    return JsonResponse({'data': getDiffs()})


def mockDays(request):
    '''
    mock data for some days 
    '''
    def mockItem(category: str):
        total = random.randint(100, 200)
        succeed = random.randint(100, total)
        return {'category': category, 'succeed': succeed, 'total': total, 'succeedRate': round(succeed / total, 2)}

    def mockDay():
        categories = ['mainline', 'epol', 'oepkgs']
        res = [mockItem(category) for category in categories]
        date = radar.random_date()
        # total: the sum of all packages
        return {'date': date, 'data': res, 'total': sum([item['total'] for item in res])}

    num_days = random.randint(5, 10)
    return JsonResponse({'data': sorted([mockDay() for _ in range(num_days)], key=lambda day: day['date'])})


def mockDevices(request):

    def mockItem():
        hostname = ''.join(random.choice(string.ascii_letters + string.digits)
                           for _ in range(random.randint(3, 7)))
        ip = '.'.join(str(random.randint(0, 256)) for _ in range(4))
        cpu_load = random.randint(0, 100)
        cpu_temp = random.randint(10, 80)
        memory_total = random.choice([2, 4, 8, 16, 32, 64])  # unit G
        memory_used = random.randint(
            (memory_total - 1) * 1024, memory_total * 1024)
        memory_used = random.randint(
            (memory_total - 1) * 1024, memory_total * 1024)
        return {'hostname': hostname, 'ip': ip, 'cpu_load': cpu_load, 'cpu_temp': cpu_temp, 'memory_total': memory_total, 'memory_used': memory_used}

    num_devices = random.randint(1, 10)
    last_update = datetime.date.today()
    return JsonResponse({'last_update': last_update, 'data': [mockItem() for _ in range(num_devices)]})
