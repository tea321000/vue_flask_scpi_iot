<template>
  <div>
    <el-container>
      <el-header>
        <el-menu class="el-menu-demo" mode="horizontal" @select="handleSelect">
          <el-submenu index="1">
            <template slot="title" v-if="roles==='visitor'">{{name}}:游客</template>
            <template slot="title" v-else-if="roles==='observer'">{{name}}:观察者</template>
            <template slot="title" v-else-if="roles==='manager'">{{name}}:管理者</template>
            <template slot="title" v-else-if="roles==='administrator'">{{name}}:管理员</template>
            <el-menu-item index="1-1">个人资料</el-menu-item>
            <el-menu-item index="1-2">退出登录</el-menu-item>
          </el-submenu>

          <el-submenu index="2">
            <template slot="title">设备</template>
            <el-menu-item index="2-1">实时设备</el-menu-item>
            <el-menu-item index="2-2">设备历史</el-menu-item>
            <el-menu-item index="2-3">用户反馈</el-menu-item>
          </el-submenu>
        </el-menu>
      </el-header>
      <el-main>
        <transition>
          <keep-alive>
            <router-view/>
          </keep-alive>
        </transition>
      </el-main>
      <el-footer></el-footer>
    </el-container>
  </div>
</template>

<script>
export default {
  data() {
    return {
      // id: this.$store.state.user.id,
      name: this.$store.state.user.name,
      roles: this.$store.state.user.roles[0]
    };
  },
  methods: {
    handleSelect(key, keyPath) {
      console.log(key, keyPath);
      if (keyPath[0] === "1") {
        if (keyPath[1] === "1-1")
          this.$router.push({ name: "PersonalPermission" });
        else if (keyPath[1] === "1-2") this.$store.dispatch("user/logout");
      } else if (keyPath[0] === "2") {
        if (keyPath[1] === "2-1") {
            this.$router.push({ name: "openDevice" });
        } else if (keyPath[1] === "2-2") {
          this.$router.push({ name: "deviceHistory" });
        }
      }
    }
  }
};
</script>