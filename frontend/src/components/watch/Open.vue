<template>
  <div>
    <h1>目前开放的设备:</h1>
    <el-collapse v-model="activeNames" @change="handleChange">
      <el-collapse-item v-for="(item,key,index) in data" :title="key" :name="index" :key="index">
        <div>设备类型：{{item.device_type}}</div>
        <div>
          设备指令集：
          <!-- <div v-for="(set,key,index) in item.device_set" :key="index">
            指令{{index+1}}：{{key}}
            <div v-for="(params,key,index) in set" :key="index">
              所需参数{{index+1}}：{{key}}
              <br>
              取值类型及范围：{{params}}
            </div>
            
          </div>-->
          <!-- <el-input placeholder="输入关键字进行过滤" v-model="filterText"></el-input> -->

          <el-tree
            class="filter-tree"
            :data="treeData[key]"
            :props="treeDefaultProps"
            default-expand-all
          ></el-tree>
          <br>
          <el-row v-if="data[key].write_permission===true">
            <el-col>
              <el-select v-model="selectCommand" filterable clearable placeholder="请选择">
                <el-option
                  v-for="item in commands[key]"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                ></el-option>
              </el-select>
            </el-col>
          </el-row>
          <br>
          <el-row v-if="data[key].write_permission===true">
            <el-col :span="16">
              <el-input
                v-model="inputParams"
                v-if="selectCommand===''"
                placeholder="请输入内容"
                @keyup.enter.native="handleCommand(key)"
              ></el-input>
              <el-input
                v-model="inputParams"
                v-else
                :placeholder="commands[key][selectCommand].params"
                @keyup.enter.native="handleCommand(key)"
              ></el-input>
            </el-col>
            <el-col :span="8">
              <el-button type="primary" @click="handleCommand(key)">
                发送
                <i class="el-icon-upload el-icon--right"></i>
              </el-button>
            </el-col>
          </el-row>
        </div>
        <br>
        <div v-if="response[key]||imageBase64.length>0">
          设备回应：
          <v-chart
            v-if="response[key]"
            :options="chart_option(key)"
            autoresize
            ref="line"
            style="width:100%;height: 100%;min-width: 300px;min-height: 600px;"
          />
          <img
            v-for="(item,index) in imageBase64"
            v-bind:src="'data:image/jpeg;base64,'+item"
            :key="index"
          >
        </div>
      </el-collapse-item>
    </el-collapse>
  </div>
</template>

<script>
import { Message } from "element-ui";
import { accAdd, accSub, accDiv, accMul } from "@/utils/floatOperate";
let Base64 = require("js-base64").Base64;
var symbolSize = 1;
export default {
  name: "open",
  data() {
    return {
      error_count:0,
      imageBase64: [],
      activeNames: [],
      data: {},
      serial_list: [],
      intervalId: 0,
      inputParams: "",
      commands: {},
      selectCommand: "",
      treeData: {},
      response: {},
      treeDefaultProps: {
        children: "children",
        label: "label"
      },
      chart_option_list: {},
      chart_option_template: {
        title: {
          text: "Try Dragging these Points"
        },
        tooltip: {
          formatter: function(params) {
            return (
              "X: " +
              params.data[0].toFixed(2) +
              "<br>Y: " +
              params.data[1].toFixed(2)
            );
          }
        },
        grid: {},
        xAxis: {
          min: 0,
          max: 1,
          type: "value",
          axisLine: { onZero: false }
        },
        yAxis: {
          min: -10,
          max: 10,
          type: "value",
          axisLine: { onZero: false }
        },
        dataZoom: [
          {
            type: "slider",
            xAxisIndex: 0,
            filterMode: "empty"
          },
          {
            type: "slider",
            yAxisIndex: 0,
            filterMode: "empty"
          },
          {
            type: "inside",
            xAxisIndex: 0,
            filterMode: "empty"
          },
          {
            type: "inside",
            yAxisIndex: 0,
            filterMode: "empty"
          }
        ],
        series: [
          {
            type: "line",
            smooth: true,
            symbolSize: symbolSize,
            data: []
          }
        ]
      }
    };
  },

  created() {
    this.getOpenDevice();
    this.intervalId = setInterval(() => {
      this.getOpenDevice();
      // console.log(this.selectCommand);
      // this.deviceSetHandler();
    }, 1000);
  },
  beforeDestroy() {
    clearInterval(this.intervalId);
  },
  watch: {
    // 同一组件原来的组件实例会被复用，所以生命周期钩子不会再被调用
    // 因此需要侦听路由变化，来加载数据
    $route(to, from) {
      if (to.name === "openDevice") this.getOpenDevice();
    },
    data: function(val, oldVal) {
      this.deviceSetHandler();
      this.responseHandler();
    }
  },
  methods: {
    handleCommand(key) {
      this.$store.state.user.serial = key;
      console.log(this.commands[key]);
      console.log(this.selectCommand);
      this.$store.state.user.command = {
        command: this.commands[key][this.selectCommand].label,
        params: this.inputParams.split(" ")
      };
      this.$store
        .dispatch("user/sendCommand")
        .then(() => {
          Message({
            message: "成功发送指令",
            type: "success",
            duration: 2 * 1000
          });
        })
        .catch(() => {
          Message({
            message: "无法发送指令，用户身份可能已过期，请尝试重新登录",
            type: "error",
            duration: 2 * 1000
          });
        });
    },

    chart_option(key) {
      if (!(key in this.chart_option_list)) {
        this.chart_option_list[key] = this.chart_option_template;
      }
      if (this.response[key]) {
        this.chart_option_list[key].series[0].data = this.response[
          key
        ].vol_data;
        this.chart_option_list[key].xAxis.max = this.response[key].time_end;
        this.chart_option_list[key].yAxis.max = this.response[key].vol_max;
        this.chart_option_list[key].yAxis.min = this.response[key].vol_min;
      }
      console.log(this.chart_option_list[key]);
      return this.chart_option_list[key];
    },
    scienceToFloat(str) {
      var str_split = str.split("e");
      if (str_split.length > 1) {
        var base = parseFloat(str_split[0]);
        var exp = parseFloat(str_split[1]);
        if (exp == 0) {
          var res_num = parseFloat(str_split[0]);
        } else {
          var res_num = Math.pow(
            parseFloat(str_split[0]),
            parseFloat(str_split[1])
          );
        }
      } else {
        var res_num = parseFloat(str);
      }
      return res_num;
    },
    responseHandler() {
      for (var device_key in this.data) {
        if (this.data[device_key].latest_response) {
          // console.log(this.data[device_key].latest_response.command);
          if (
            !this.response[device_key] ||
            this.response[device_key].id !=
              this.data[device_key].latest_response_id
          ) {
            // console.log(this.data[device_key].latest_response_command);
            if (
              this.data[device_key].latest_response_command.command ==
              "采集波形"
            ) {
              // console.log(
              //   this.data[device_key].latest_response.vol_data.slice(2, -1)
              // );
              var sample_time = this.scienceToFloat(
                this.data[device_key].latest_response.sample_time
              );
              var vol_max = this.scienceToFloat(
                this.data[device_key].latest_response.vol_max
              );
              var vol_min = this.scienceToFloat(
                this.data[device_key].latest_response.vol_min
              );
              // console.log(vol_max_str);
              // console.log(vol_min_str);
              // console.log(parseInt(sample_time_str[0]));
              // console.log(parseInt(sample_time_str[1]));
              // var sample_time = Math.pow(
              //   parseFloat(sample_time_str[0]),
              //   parseFloat(sample_time_str[1])
              // );
              // var vol_max = Math.pow(
              //   parseFloat(vol_max_str[0]),
              //   parseFloat(vol_max_str[1])
              // );
              // var vol_min = Math.pow(parseFloat(vol_min_str[0]), 1);
              // console.log(sample_time);
              // console.log(parseFloat(vol_min_str[0]));
              // console.log(parseFloat(vol_min_str[1]));
              // console.log(vol_max);
              // console.log(vol_min);

              // console.log(sample_time);
              var vol_data_str = Base64.decode(
                this.data[device_key].latest_response.vol_data.slice(2, -1)
              );
              // console.log(vol_data_str.length);
              var vol_data = [];
              var ad_max = -Infinity,
                ad_min = Infinity;
              for (var index = 0; index < vol_data_str.length; index++) {
                if (vol_data_str.charCodeAt(index) > ad_max) {
                  ad_max = vol_data_str.charCodeAt(index);
                } else if (vol_data_str.charCodeAt(index) < ad_min) {
                  ad_min = vol_data_str.charCodeAt(index);
                }
                vol_data.push([
                  index * sample_time,
                  vol_data_str.charCodeAt(index)
                ]);
              }

              var coefficient = accDiv(
                accSub(vol_max, vol_min),
                accSub(ad_max, ad_min)
              );
              // console.log(vol_max);
              // console.log(vol_min);
              // console.log(accSub(vol_max, vol_min));
              // console.log(accSub(ad_max, ad_min));
              // console.log(coefficient);

              vol_data = vol_data.map(function(row) {
                // return [row[0], (row[1] - ad_min) * coefficient + vol_min];
                return [
                  row[0],
                  accAdd(accMul(accSub(row[1], ad_min), coefficient), vol_min)
                ];
              });
              // console.log(vol_data[0]);
              // console.log(max_ad);
              // console.log(min_ad);
              // console.log(this.data[device_key].latest_response.vol_max);
              // console.log(this.data[device_key].latest_response.vol_min);

              this.response[device_key] = {
                id: this.data[device_key].latest_response_id,
                command: "采集波形",
                vol_data: vol_data,
                vol_max: vol_max,
                vol_min: vol_min,
                time_end: vol_data_str.length * sample_time
              };

              console.log(this.response[device_key]);
            } else if (
              this.data[device_key].latest_response_command.command == "重建"
            ) {
              this.imageBase64 = [];
              this.imageBase64[0] = this.data[
                device_key
              ].latest_response.frameL;
              this.imageBase64[1] = this.data[
                device_key
              ].latest_response.frameR;
              this.imageBase64[2] = this.data[
                device_key
              ].latest_response.reconstruction;
              // console.log(this.imageBase64);
            } else if (
              this.data[device_key].latest_response_command.command == "拍照"
            ) {
              this.imageBase64 = [];
              this.imageBase64[0] = this.data[
                device_key
              ].latest_response.frameL;
              this.imageBase64[1] = this.data[
                device_key
              ].latest_response.frameR;
              // console.log(this.imageBase64);
            }
          }
        }
      }
    },
    deviceSetHandler() {
      // console.log(this.data.device_set);
      // this.treeData = {};
      // this.commands = {};
      for (var device_key in this.data) {
        // console.log(this.data[device_key].latest_response);
        if (this.serial_list.indexOf(device_key) == -1) {
          var device_set = [];
          var commands = [];
          var command_count = 1;
          // console.log(this.data[device_key].device_set);

          for (var command_key in this.data[device_key].device_set) {
            // console.log(command_key);
            var command = {
              label: "指令" + String(command_count) + "： " + command_key,
              children: []
            };

            var params_count = 1;
            var commands_params = "参数：";
            // console.log(this.data[device_key].device_set[command_key]);
            for (var params_key in this.data[device_key].device_set[
              command_key
            ]) {
              var params = {
                label:
                  "参数" +
                  String(params_count) +
                  "： " +
                  params_key +
                  "   取值类型及范围：" +
                  this.data[device_key].device_set[command_key][params_key]
              };
              command.children.push(params);
              commands_params += params_key + " ";
              params_count += 1;
            }
            commands.push({
              label: command_key,
              value: command_count - 1,
              params: commands_params
            });
            device_set.push(command);
            command_count += 1;
          }
          // console.log(device_set);
          this.treeData[device_key] = device_set;
          this.commands[device_key] = commands;
          this.serial_list.push(device_key);
        }
      }
      return Promise.resolve();
    },
    getOpenDevice() {
      this.$store
        .dispatch("user/queryDevices")
        .then(data => {
          // Message({
          //   message: "成功获取设备信息",
          //   type: "success",
          //   duration: 2 * 1000
          // });
          this.error_count=0;
          console.log(data);
          this.data = data;
        })
        .catch(() => {
          this.error_count+=1;
          console.log(this.error_count)
          if(this.error_count>3)
          {
            Message({
            message: "无法获取设备信息，用户身份可能已过期，请尝试重新登录",
            type: "error",
            duration: 2 * 1000
          });
            this.error_count=0;
          }
          
          
        });
    },
    handleChange(val) {
      console.log(val);
    }
  }
};
</script>
<style scoped>
/* .el-select .el-input {
  width: 130px;
}
.input-with-select .el-input-group__prepend {
  background-color: #fff;
} */
</style>