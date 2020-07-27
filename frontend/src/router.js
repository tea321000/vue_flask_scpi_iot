import Vue from 'vue'
import Router from 'vue-router'
import Home from './views/Home'
import Login from './views/login.vue'

Vue.use(Router)

// export default new Router({
//   mode: 'history',
//   base: process.env.BASE_URL,
//   routes: [{
//       path: '/',
//       name: 'home',
//       component: Home

//     },
//     {
//       path: '/login',
//       name: 'login',
//       component: Login
//     },
//     {
//       path: '/about',
//       name: 'about',
//       // route level code-splitting
//       // this generates a separate chunk (about.[hash].js) for this route
//       // which is lazy-loaded when the route is visited.
//       component: function () {
//         return import( /* webpackChunkName: "about" */ './views/About.vue')
//       }
//     }
//   ]
// })


/** note: sub-menu only appear when children.length>=1
 *  detail see  https://panjiachen.github.io/vue-element-admin-site/guide/essentials/router-and-nav.html
 **/

/**
* hidden: true                   if `hidden:true` will not show in the sidebar(default is false)
* alwaysShow: true               if set true, will always show the root menu, whatever its child routes length
*                                if not set alwaysShow, only more than one route under the children
*                                it will becomes nested mode, otherwise not show the root menu
* redirect: noredirect           if `redirect:noredirect` will no redirect in the breadcrumb
* name:'router-name'             the name is used by <keep-alive> (must set!!!)
* meta : {
    roles: ['admin','editor']    will control the page roles (you can set multiple roles)
    title: 'title'               the name show in sub-menu and breadcrumb (recommend set)
    icon: 'svg-name'             the icon show in the sidebar
    noCache: true                if true, the page will no be cached(default is false)
    breadcrumb: false            if false, the item will hidden in breadcrumb(default is true)
    affix: true                  if true, the tag will affix in the tags-view
  }
**/

/**
 * constantRoutes
 * a base page that does not have permission requirements
 * all roles can be accessed
 * */
export const constantRoutes = [{
    path: '/login',
    name: 'login',
    component: Login
  },

  // {
  //   path: '/404',
  //   component: () => import('@/views/errorPage/404'),
  //   hidden: true
  // },
  // {
  //   path: '/401',
  //   component: () => import('@/views/errorPage/401'),
  //   hidden: true
  // }
]

/**
 * asyncRoutes
 * the routes that need to be dynamically loaded based on user roles
 */
export const asyncRoutes = [{
  path: '/',
  component: Home,
  meta: {
    title: 'permission',
    roles: ['observer', 'manager','administrator'] // you can set roles in root nav
  },
  children: [{
      path: '/',
      component: function () {
        return import( /* webpackChunkName: "Home" */ './views/Index')
      },
      name: 'IndexPermission',
      meta: {
        title: 'IndexPermission',
        roles: ['observer', 'manager','administrator'] // you can set roles in root nav
      }
    },
    {
      path: 'personal',
      component: function () {
        return import( /* webpackChunkName: "Home" */ './views/Personal')
      },
      name: 'PersonalPermission',
      meta: {
        title: 'PersonalPermission',
        roles: ['observer', 'manager','administrator'] // you can set roles in root nav
        // roles: ['admin'] // or you can only set roles in sub nav
      }
    },
    // {
    //   path: '/layout',
    //   component: resolve => require(['./views/Layout'], resolve),
    //   // function () {
    //   //   return import( resolve => require(['./views/Feedback'], resolve),)
    //   // },
    //   name: 'LayoutPermission',
    //   meta: {
    //     title: 'LayoutPermission',
    //     roles: ['visitor', 'observer', 'manager', 'administrator'] // you can set roles in root nav
    //   }
    // },

    {
      path: 'watch',
      component: function () {
        return import( /* webpackChunkName: "WATCH" */ './views/Watch')
      },
      meta: {
        title: 'watch',
      },
      children: [{
          path: 'open',
          component: function () {
            return import( /* webpackChunkName: "WATCH" */ './views/watch/Open')
          },
          name: 'openDevice',
          meta: {
            title: 'openDevice',
          }
        },
        
        {
          path: 'history',
          component: function () {
            return import( /* webpackChunkName: "WATCH" */ './views/watch/History')
          },
          name: 'deviceHistory',
          meta: {
            title: 'deviceHistory',
            roles: ['observer','manager', 'administrator']
          }
        },
      ]
    },
    
  ]
}]



const createRouter = () => new Router({
  mode: 'history', // require service support
  scrollBehavior: () => ({
    y: 0
  }),
  routes: constantRoutes
})

const router = createRouter()

// Detail see: https://github.com/vuejs/vue-router/issues/1234#issuecomment-357941465
export function resetRouter() {
  const newRouter = createRouter()
  router.matcher = newRouter.matcher // reset router
}

export default router