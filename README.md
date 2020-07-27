# vue_flask_scpi_iot
包括：基于vue_admin_template的vue+flask前后端分离仪器线上监测及操作平台、树莓派基于request与后端交互程序、树莓派电源板、树莓派亚克力外壳设计四部分。

树莓派终端使用SCPI指令对信号发生器以及示波器等测试仪器进行无人操作并传输到网站后端，用户可在web页面上动态操作在线的仪器并返回测试结果

使用方法：

1、前端frontend主要通过request.js的baseURL来与后端进行通信，需要更改为自己的域名和端口；

2、后端wechat_server需要更改app.py的port

3、树莓派instr_request_website需要配置server_address

4、前端根据vue_cli脚手架进行构建，根据frontend文件夹里的package.json安装相关依赖，然后输入vue ui在图形化界面中build生产环境，会在frontend文件夹下生成dist文件夹；

5、将dist文件夹复制到wechat_server文件夹下，完成所有配置。部署可以使用gunicorn+nginx进行部署


![整体架构](https://github.com/tea321000/vue_flask_scpi_iot/blob/master/imgs/A0%E5%9B%BE%E7%BA%B8-1.png "整体架构")

![树莓派终端线上注册逻辑](https://github.com/tea321000/vue_flask_scpi_iot/blob/master/imgs/A0%E5%9B%BE%E7%BA%B8-5.png "树莓派终端线上注册逻辑")

![用户注册逻辑](https://github.com/tea321000/vue_flask_scpi_iot/blob/master/imgs/A0%E5%9B%BE%E7%BA%B8-5.png "用户注册逻辑")

![用户注册逻辑](https://github.com/tea321000/vue_flask_scpi_iot/blob/master/imgs/A0%E5%9B%BE%E7%BA%B8-6.png "用户注册逻辑")

![用户登录逻辑](https://github.com/tea321000/vue_flask_scpi_iot/blob/master/imgs/A0%E5%9B%BE%E7%BA%B8-7.png "用户登录逻辑")

![设备动态显示逻辑](https://github.com/tea321000/vue_flask_scpi_iot/blob/master/imgs/A0%E5%9B%BE%E7%BA%B8-8.png "设备动态显示逻辑")

![树莓派电源板原理图](https://github.com/tea321000/vue_flask_scpi_iot/blob/master/imgs/A0%E5%9B%BE%E7%BA%B8-2.png "树莓派电源板原理图")

![树莓派电源板PCB](https://github.com/tea321000/vue_flask_scpi_iot/blob/master/imgs/A0%E5%9B%BE%E7%BA%B8-3.png "树莓派电源板PCB")

![树莓派亚克力外壳](https://github.com/tea321000/vue_flask_scpi_iot/blob/master/imgs/A0%E5%9B%BE%E7%BA%B8-4.jpg "树莓派亚克力外壳")


