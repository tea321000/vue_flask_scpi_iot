<template>
  <div>
    <h1>设备历史</h1>
    <el-row>
      请选择设备：
      <el-select
        v-model="selectDevice"
        filterable
        clearable
        placeholder="CPU序列号"
        @change="selectDeviceChange"
      >
        <el-option v-for="(item,key,index) in data" :key="index" :label="key" :value="key"></el-option>
      </el-select>
    </el-row>
    <br>
    <div v-if="selectDevice!=''&&data[selectDevice].read_permission===true">
      <el-row>
        请选择要查询的历史信息：
        <el-select
          v-model="selectHistory"
          filterable
          clearable
          placeholder="历史记录"
          style="width:100%;"
        >
          <el-option
            v-for="(item,key,index) in data[selectDevice].history"
            :key="index"
            :label="item|historyFormatter"
            :value="item.id"
          ></el-option>
        </el-select>
      </el-row>
      <br>
      <el-row>
        <el-button type="primary" @click="QueryHistoryDetail(selectHistory)">
          查询历史详情
          <i class="el-icon-upload el-icon--right"></i>
        </el-button>
      </el-row>
    </div>
    <el-row v-else-if="selectDevice!=''&&data[selectDevice].read_permission===false">
      <h3 style="color:red">您没有权限查看此设备历史</h3>
    </el-row>
    <br>
    <!-- {{data[selectDevice]}} -->
    <div v-if="data[selectDevice]&&data[selectDevice].device_type.indexOf('image')>-1">
      <el-row v-if="history_response!=''&&history_response.command.command=='重建'">
        <img v-bind:src="'data:image/jpeg;base64,'+history_response.response.frameL">
        <img v-bind:src="'data:image/jpeg;base64,'+history_response.response.frameR">
        <img v-bind:src="'data:image/jpeg;base64,'+history_response.response.reconstruction">
      </el-row>
      <el-row v-else-if="history_response!=''&&history_response.command.command=='拍照'">
        <img v-bind:src="'data:image/jpeg;base64,'+history_response.response.frameL">
        <img v-bind:src="'data:image/jpeg;base64,'+history_response.response.frameR">
      </el-row>
    </div>
    <div v-if="data[selectDevice]&&data[selectDevice].device_type.indexOf('wave')>-1">
      <el-row v-if="history_response!=''&&history_response.command.command=='采集波形'">
        <v-chart
          v-if="history_response.response.vol_data"
          :options="chart"
          autoresize
          ref="line"
          style="width:100%;height: 100%;min-width: 300px;min-height: 600px;"
        />
      </el-row>
    </div>
  </div>
</template>

<script>
import { Message } from "element-ui";
import { accAdd, accSub, accDiv, accMul } from "@/utils/floatOperate";
let Base64 = require("js-base64").Base64;
var symbolSize = 1;
export default {
  name: "history",
  data() {
    return {
      data: [],
      selectDevice: "",
      selectHistory: "",
      history_response: "",
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
  computed: {
    chart: function() {
      // console.log(this.history_response.response);
      var sample_time = this.scienceToFloat(
        this.history_response.response.sample_time
      );
      var vol_max = this.scienceToFloat(this.history_response.response.vol_max);
      var vol_min = this.scienceToFloat(this.history_response.response.vol_min);
      var vol_data_str = Base64.decode(
        this.history_response.response.vol_data.slice(2, -1)
      );
      var vol_data = [];
      var ad_max = -Infinity,
        ad_min = Infinity;
      for (var index = 0; index < vol_data_str.length; index++) {
        if (vol_data_str.charCodeAt(index) > ad_max) {
          ad_max = vol_data_str.charCodeAt(index);
        } else if (vol_data_str.charCodeAt(index) < ad_min) {
          ad_min = vol_data_str.charCodeAt(index);
        }
        vol_data.push([index * sample_time, vol_data_str.charCodeAt(index)]);
      }
      var coefficient = accDiv(
        accSub(vol_max, vol_min),
        accSub(ad_max, ad_min)
      );
      vol_data = vol_data.map(function(row) {
        // return [row[0], (row[1] - ad_min) * coefficient + vol_min];
        return [
          row[0],
          accAdd(accMul(accSub(row[1], ad_min), coefficient), vol_min)
        ];
      });
      this.chart_option_template.series[0].data = vol_data;
      this.chart_option_template.xAxis.max = vol_data_str.length * sample_time;
      this.chart_option_template.yAxis.min = vol_min;

      // this.response[device_key] = {
      //           id: this.data[device_key].latest_response_id,
      //           command: "采集波形",
      //           vol_data: vol_data,
      //           vol_max: vol_max,
      //           vol_min: vol_min,
      //           time_end: vol_data_str.length * sample_time
      //         };
      return this.chart_option_template;
    }
  },
  filters: {
    historyFormatter(item) {
      if (item.command.params != "") {
        var params = item.command.params;
      } else {
        var params = "无";
      }
      var time = new Date(item.timestamp);
      var year = time.getFullYear();
      var month = time.getMonth() + 1;
      var date = time.getDate();
      var hour = time.getHours();
      var min = time.getMinutes();
      var second = time.getSeconds();
      return (
        "时间：" +
        year +
        "年" +
        month +
        "月" +
        date +
        "日" +
        hour +
        "时" +
        min +
        "分" +
        second +
        "秒,指令：" +
        item.command.command +
        ",参数：" +
        params
      );
    }
  },
  created() {
    this.getDeviceHistory();
  },
  methods: {
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
    getDeviceHistory() {
      this.$store
        .dispatch("user/deviceHistory")
        .then(data => {
          console.log(data);
          this.data = data;
        })
        .catch(() => {
          Message({
            message: "无法获取设备历史，用户身份可能已过期，请尝试重新登录",
            type: "error",
            duration: 2 * 1000
          });
        });
    },
    QueryHistoryDetail(id) {
      this.$store.state.user.device_history_id = id;
      this.$store
        .dispatch("user/deviceHistoryDetail")
        .then(data => {
          console.log(data);
          this.history_response = data;
        })
        .catch(() => {
          Message({
            message: "无法获取设备历史详情，用户身份可能已过期，请尝试重新登录",
            type: "error",
            duration: 2 * 1000
          });
        });
    },
    selectDeviceChange() {
      this.selectHistory = "";
    }
  },
  watch: {
    // 同一组件原来的组件实例会被复用，所以生命周期钩子不会再被调用
    // 因此需要侦听路由变化，来加载数据
    $route(to, from) {
      if (to.name === "deviceHistory") this.getDeviceHistory();
    }
  }
};
</script>

