from __future__ import print_function
import visa
import sys
import time
import requests
import uuid
import time
import os
import json
import asyncio
import base64
import matplotlib.pyplot as plt
from collections import OrderedDict
import logging
logging.basicConfig(filename='debug.log', level=logging.DEBUG,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(message)s', datefmt='%Y-%m-%d')


memory_depth_list = (14000, 140000, 1400000, 14000000, 56000000)


init_flag = False
server_address = 'subdomain.yourdomain.xyz'
os.environ['NO_PROXY'] = server_address
http_header = 'https://'
headers = {'Content-Type': 'application/json'}
token = ""
oscilloscope_set = {'采集波形': 'dataCollet', '采集频率': 'frequencyCollect'}
generator_set = {'生成波形': 'generateWave'}
response_list = []
done_id_list = []
running_id_list = []


@asyncio.coroutine
def command_parse(query_content):
    if query_content['content']['command'] in oscilloscope_set.keys():
        print('新建示波器对象实例')
        oscilloscope_object = oscilloscopeObject()

        # yield from suspends execution until
        # there's some result from asyncio.sleep
        try:
            print(oscilloscope_set[query_content['content']['command']])
            print(query_content['content']['params'])
            method = getattr(oscilloscope_object,
                             oscilloscope_set[query_content['content']['command']])
            response = method(query_content['content']['params'])
            oscilloscope_object.close()
            print("终止示波器连接")
            # oscilloscope_object.dataCollet(2)
        except UnicodeDecodeError:
            sys.stderr.write('数据获取太频繁,请重启仪器')
            sys.exit()
    elif query_content['content']['command'] in generator_set.keys():
        print('新建信号发生器对象实例')
        generator_object = generatorObject()

        # yield from suspends execution until
        # there's some result from asyncio.sleep
        try:
            print(generator_set[query_content['content']['command']])
            print(query_content['content']['params'])
            method = getattr(generator_object,
                             generator_set[query_content['content']['command']])
            response = method(query_content['content']['params'])
            print("终止信号发生器连接")
            generator_object.close()
        except UnicodeDecodeError:
            sys.stderr.write('数据获取太频繁,请重启仪器')
            sys.exit()
    return {'id': query_content['id'], 'response': response}
    # return {'id': query_content['id'], 'status': 'success', 'response': response}
    # return 'Future is done!vol_max:'+oscilloscope_object.vol_max+'vol_min:'+oscilloscope_object.vol_min+'vol_data:'


def got_result(future):
    # global oscilloscope_object
    # print(future.result())
    global response_list
    response_list.append(future.result())
    if future.result()['id'] not in done_id_list:
        done_id_list.append(future.result()['id'])
        running_id_list.remove(future.result()['id'])

    # print(oscilloscope_object.vol_data)


class generatorObject(object):
    def __init__(self):
        rm = visa.ResourceManager()
        try:
            self.generator = rm.open_resource(rm.list_resources(
                "?*DG")[0])  # 搜索带有DG字符串的元素，打开RIGOL的DG系列信号发生器
        except IndexError:
            sys.stderr.write("没有插入信号发生器或没有开启信号发生器")
            sys.exit()

    def query(self, message):
        return self.generator.query(message)

    def write(self, message):
        self.generator.write(message)

    def close(self):
        self.generator.close()
        del self

    def generateWave(self, params):
        # [wave, frequency, amplitude, offset]
        length = len(params)

        if length >= 1 and length <= 4:
            wave_set = {'正弦波': 'SIN', '方波': 'SQU',
                        '三角波': 'RAMP', '脉冲': 'PULS', '噪声': 'NOIS', '直流': 'DC'}
            self.write('VOLT:UNIT VPP')
            if params[0] in wave_set.keys():
                if length == 1:
                    self.write(
                        'APPL:'+wave_set[params[0]])
                elif length == 2:
                    frequency = params[1]
                    self.write(
                        'APPL:'+wave_set[params[0]]+' '+frequency)
                elif length == 3:
                    frequency = params[1]
                    amplitude = params[2]
                    self.write(
                        'APPL:'+wave_set[params[0]]+' '+frequency+','+amplitude)
                elif length == 4:
                    frequency = params[1]
                    amplitude = params[2]
                    offset = params[3]
                    self.write(
                        'APPL:'+wave_set[params[0]]+' '+frequency+','+amplitude+','+offset)
                self.write('OUTP ON')
                return {'bool': True}
            else:
                sys.stderr.write("输入信息有误")
                return {'bool': False}


class oscilloscopeObject(object):
    def __init__(self):
        rm = visa.ResourceManager()
        try:
            self.oscilloscope = rm.open_resource(rm.list_resources(
                "?*DS")[0])  # 搜索带有DS字符串的元素，打开RIGOL的DS系列示波器
        # rm.list_resources()的API有自身特有的正则表达式表示，与Python的普通正则表达式表示方法不同。
        except IndexError:
            sys.stderr.write("没有插入示波器或没有开启示波器")
            sys.exit()
        else:
            self.getWaveParams()
            self.setDefaults(1)

    def query(self, message):
        return self.oscilloscope.query(message)

    def write(self, message):
        self.oscilloscope.write(message)

    def query_binary(self, message):
        return self.oscilloscope.query_binary_values(
            message, datatype='B', header_fmt='ieee', is_big_endian=False)

    def run(self):
        self.write(":RUN")

    def stop(self):
        self.write(":STOP")

    def close(self):
        self.oscilloscope.close()
        del self

    def reset(self):
        self.write(":SYST:RES")

    def setMemoryDepth(self, memory_depth):
        if(memory_depth not in memory_depth_list):
            raise RuntimeError('输入的采样率不正确')
        self.write(":ACQ:MDEP "+str(memory_depth))

    def setDefaults(self, channel):
        self.write(':WAV:SOUR CHAN'+str(channel))
        self.write(':WAV:MODE NORM')
        self.write(':WAV:FORM BYTE')
        self.write(':ACQ:TYPE AVER')

    def getWaveformTime(self):
        # get time increment of horizontal axis
        self.xinc = self.query(':WAV:XINC?')
        # get the zero position of horizontal axis
        self.xoffs = self.query(':TIM:OFFS?')
        # get number of pointson horizontal axis
        self.point_nr = self.query(':WAV:POIN?')
        # get the horizontal scale of small square on the screen (there are 14 of them)
        self.xscal = self.query(':TIM:SCAL?')
        # below: create numpy array of time points and crop it if there are too much points
        # self.timeAxis = np.arange(-(7-self.xoffs/self.xscal)
        #                           * self.xscal, 14*self.xscal, self.xinc)[0:self.point_nr]

    def getVolParams(self):
        """These are needed to convert waveform data to voltage"""

        self.YRef = self.query(':WAV:YREF?')
        self.YScale = self.query(':CHAN1:SCAL?')
        self.YOffset = self.query(':CHAN1:OFFS?')

    def getWaveParams(self):
        self.getWaveformTime()
        self.getVolParams()

    # def cvtData2Voltage(self, data):
    #         """data must be numpy array of pandas dataframe
    #         the conversion formula was taken from scope programming guide, page 572
    #     http://int.rigol.com/Support/Manual/5 """
    #         result=(data-self.YRef)*self.YScale-self.YOffset
    #         return result

    def frequencyCollect(self, params):
        self.write(':MEAS:COUN:SOUR  CHAN'+params[0])
        self.frequency = self.query(':MEAS:COUN:VAL?')
        frequency = float(self.frequency[:self.frequency.find('\n')])
        return {'frequency': frequency}

    # def voltageCollet(self, channel):
    #     # self.write(':AUToscale')
    #     self.write(':AUToscale')
    #     self.ChannelManager(channel[0])
    #     time.sleep(3)
    #     self.vol_max = self.query(":MEASure:VMAX? CHAN"+channel[0])
    #     # 打开通道X的幅度最小值测量功能，并返回测量结果。
    #     self.vol_min = self.query(":MEASure:VMIN? CHAN"+channel[0])
    #     vol_max = float(self.vol_max[:self.vol_max.find('\n')])
    #     vol_min = float(
    #         self.vol_min[:self.vol_min.find('\n')])
    #     return {'vol_max': vol_max, 'vol_min': vol_min}

    def dataCollet(self, params):
        self.write(':AUToscale')
        self.ChannelManager(params[0])
        time.sleep(3)
        self.vol_max = self.query(":MEASure:VMAX? CHAN"+params[0])
        self.vol_min = self.query(":MEASure:VMIN? CHAN"+params[0])

        self.write(':WAV:SOUR CHAN'+params[0])
        # self.write(':WAV:STAR 1')
        # self.write(':WAV:STOP 1400')

        self.vol_data = self.query_binary(':WAV:DATA?')
        vol_max_num = max(self.vol_data)
        vol_min_num = min(self.vol_data)
        vol_max = float(self.vol_max[:self.vol_max.find('\n')])
        vol_min = float(
            self.vol_min[:self.vol_min.find('\n')])
        coefficient = (vol_max-vol_min)/(vol_max_num-vol_min_num)
        sample_time = float(self.xinc[:self.xinc.find('\n')])
        print(vol_max)
        print(vol_min)
        print(coefficient)
        print(sample_time)
        wave = []
        wave_time = []
        wave_time_now = 0
        for vol in self.vol_data:
            wave_time.append(wave_time_now)
            val = (vol-vol_min_num)*coefficient+vol_min
            wave.append(val)
            wave_time_now += sample_time
        plt.clf()
        plt.title("vol_wave:")
        plt.plot(wave_time, wave, color='green')
        plt.draw()
        vol = [[0]*2 for i in range(len(self.vol_data))]
        k = 0
        for i, j in zip(wave_time, wave):
            vol[k][0] = i
            vol[k][1] = j
            k += 1
        # print(vol)

        print(len(self.vol_data))
        # print(base64.b64encode(b''.join(self.vol_data))[:100])
        vol_data = str(base64.b64encode(bytes(self.vol_data)))
        print(len(vol_data))
        # print(vol_data[:100])
        return {'vol': vol, 'vol_max': vol_max, 'time_end': wave_time[-1], 'vol_min': vol_min}

    def ChannelManager(self, channel_str):
        channel = int(channel_str)
        if channel == 0:
            self.write(":CHAN1:DISP ON")
            self.write(":CHAN2:DISP ON")
        elif channel == 1:
            self.write(":CHAN1:DISP ON")
            self.write(":CHAN2:DISP OFF")
        elif channel == 2:
            self.write(":CHAN1:DISP OFF")
            self.write(":CHAN2:DISP ON")
        else:
            self.write(":CHAN1:DISP OFF")
            self.write(":CHAN2:DISP OFF")


def getSerial():
    # Extract serial from cpuinfo file
    cpuserial = "0000000000000000"
    try:
        f = open('/proc/cpuinfo', 'r')
        for line in f:
            if line[0:6] == 'Serial':
                cpuserial = line[10:26]
        f.close()
    except:
        cpuserial = "ERROR"
    return cpuserial


def getDeviceInfo():
    serial = getSerial()
    # print(serial)
    if serial == "ERROR":
        sys.stderr.write("您使用的设备CPU没有序列号，自动退出")
        sys.exit()
    my_uuid = str(uuid.uuid1())
    # print(my_uuid)
    mac_index = my_uuid.rfind('-', 0, len(my_uuid))
    mac = my_uuid[mac_index+1:]
    # print(mac)
    device_type = ['wave']
    # device_set = {"采集波形": {"通道": "从1到2"}, "采集电压": {"通道": "从1到2"},"生成波形": {"波形": [
    #     "正弦波", "方波", "三角波", "脉冲", "噪声", "直流"], "频率": "0到25000000HZ", "振幅": "0到20.0V", "偏移": "最大振幅的一半"}}
    device_set = OrderedDict([("采集波形", {"通道": "从1到2"}), ("采集频率", {"通道": "从1到2"}), ("生成波形", OrderedDict([("波形", [
        "正弦波", "方波", "三角波", "脉冲", "噪声", "直流"]), ("频率", "0到25000000HZ"), ("振幅", "0到20.0V"), ("偏移", "最大振幅的一半")]))])
    # device_set = OrderedDict([("采集波形", {"通道": "从1到2"}), ("采集电压", {"通道": "从1到2"}), ("生成波形", {"波形": [
    #     "正弦波", "方波", "三角波", "脉冲", "噪声", "直流"], "频率":"0到25000000HZ", "振幅":"0到20.0V", "偏移":"最大振幅的一半"})])
    print(device_set)
    permission = 5
    # return {'serial': serial, 'mac': mac, 'device_type': device_type, 'device_set': device_set, 'permission': permission}
    return OrderedDict([('serial', serial), ('mac', mac), ('device_type', device_type), ('device_set', device_set), ('permission', permission)])


if __name__ == "__main__":
    mng = plt.get_current_fig_manager()
    mng.window.showMaximized()
    plt.ion()
    plt.show()
    pre = int(time.time())
    while True:
        plt.pause(0.001)
        now = int(time.time())
        if now-pre > 1:
            if not token:
                print("没有token")
                print(http_header+server_address +
                      '/automation/device_register')
                r = requests.post(http_header+server_address +
                                  '/automation/device_register', headers=headers, data=json.dumps(getDeviceInfo()))
                print(r)
                if r.status_code is 200:
                    token = r.json()['data']['device_token']
                    print(token)
            else:
                print("有token")
                r = requests.post(http_header+server_address +
                                  '/automation/device',  headers=headers, data=json.dumps({'device_token': token, 'response': response_list}))
                if r.status_code is 200:
                    response_list = []
                    res = r.json()['data']['commands']
                    print(res)
                    # print(done_id_list)
                    res_backup = []
                    for item in res:
                        if item['id'] not in done_id_list and item['id'] not in running_id_list:
                            res_backup.append(item)

                            # print(running_id_list)
                    res = res_backup
                    if res:
                        print('当前任务:')
                        print(res[0])
                        running_id_list.append(res[0]['id'])
                        loop = asyncio.get_event_loop()
                        task = loop.create_task(
                            command_parse(res[0]))
                        task.add_done_callback(got_result)
                        loop.run_until_complete(task)
                elif r.status_code is not 200:
                    token = ""
                    r = requests.post(http_header+server_address +
                                      '/automation/device_register', headers=headers, data=json.dumps(getDeviceInfo()))
                # elif r.status_code is 200 and not init_flag:
                #     res=r.json()['data']['commands']
                #     for item in res:
                #         running_id_list.append(item['id'])
                #         done_id_list.append(item['id'])
                #         init_flag=True

            pre = int(time.time())
