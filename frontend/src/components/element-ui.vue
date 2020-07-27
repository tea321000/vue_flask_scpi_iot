<template>
  <div id="app">
    <el-button @click="visible = true">Button</el-button>
    <el-dialog :visible.sync="visible" title="Hello world">
      <p>Try Element{{msg}}</p>
    </el-dialog>
  </div>
</template>

<script>
export default {
  name: "ElementPage",
  data() {
    return {
      visible: false
    };
  },
  props: {
    msg: String
  }
};
</script>