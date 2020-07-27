<template>
  <div>
    <div v-if="roles==='visitor'" center>
      <h1 center>欢迎您，游客！</h1>
    </div>
    <div v-if="roles==='observer'" center>
      <h1 center>欢迎您，编号为{{id}}的{{name}}观察者！</h1>
    </div>
    <div v-else-if="roles==='manager'" center>
      <h1>欢迎您，编号为{{id}}的{{name}}管理者！</h1>
    </div>
    <div v-else-if="roles==='administrator'" center>
      <h1>欢迎您，编号为{{id}}的{{name}}超级管理员！</h1>
    </div>
  </div>
</template>

<script>
export default {
  name: "index",
  data() {
    return {
      id: this.$store.state.user.id,
      name: this.$store.state.user.name,
      roles: this.$store.state.user.roles[0]
    };
  }
};
</script>

