import {
    login,
    register,
    logout,
    getInfo,
    personalChange,
    queryDevices,
    sendCommand,
    deviceHistory,
    deviceHistoryDetail
} from '@/api/user'
import {
    getToken,
    setToken,
    removeToken
} from '@/utils/auth'
import router, {
    resetRouter
} from '@/router'

const state = {
    token: getToken(),
    id: '',
    name: '',
    birthday: '',
    phone: '',
    roles: [],
    serial: "",
    command: {},
    device_history_id:""
}

const mutations = {
    SET_TOKEN: (state, token) => {
        state.token = token
    },
    SET_PHONE: (state, phone) => {
        state.phone = phone
    },
    SET_ID: (state, id) => {
        state.id = id
    },
    SET_NAME: (state, name) => {
        state.name = name
    },
    SET_BIRTHDAY: (state, birthday) => {
        state.birthday = birthday
    },
    SET_ROLES: (state, roles) => {
        state.roles = roles
    },
}

const actions = {
    // user login
    login({
        commit
    }, userInfo) {
        const {
            username,
            password
        } = userInfo
        return new Promise((resolve, reject) => {
            login({
                username: username.trim(),
                password: password
            }).then(response => {
                const {
                    data
                } = response
                console.log(data)
                commit('SET_TOKEN', data.token)
                setToken(data.token)
                resolve()
            }).catch(error => {
                reject(error)
            })
        })
    },
    register({
        commit
    }, userInfo) {
        const {
            username,
            name,
            password,
            birthday,
            phone,
            role
        } = userInfo
        return new Promise((resolve, reject) => {
            register({
                username: username.trim(),
                name: name.trim(),
                password: password,
                birthday: birthday,
                phone: phone,
                role: role

            }).then(response => {
                const {
                    data
                } = response
                // console.log(data)
                resolve()
            }).catch(error => {
                reject(error)
            })
        })
    },
    personalChange({
        commit,
        state
    }, userInfo) {
        const {
            password,
            birthday,
            phone
        } = userInfo
        return new Promise((resolve, reject) => {
            personalChange({
                password: password,
                birthday: birthday,
                phone: phone,
                token: state.token
            }).then(response => {
                const {
                    data
                } = response
                // console.log(data)
                resolve()
            }).catch(error => {
                reject(error)
            })
        })
    },



    // get user info
    getInfo({
        commit,
        state
    }) {
        return new Promise((resolve, reject) => {

            getInfo({
                token: state.token
            }).then(response => {
                const {
                    data
                } = response


                if (!data) {
                    reject('认证失败，请重新登录')
                }

                const {
                    roles,
                    name,
                    birthday,
                    phone,
                    id
                } = data
                // roles must be a non-empty array
                if (!roles || roles.length <= 0) {
                    reject('getInfo: roles must be a non-null array!')
                }
                commit('SET_ROLES', roles)
                commit('SET_NAME', name)
                commit('SET_BIRTHDAY', birthday)
                commit('SET_PHONE', phone)
                commit('SET_ID', id)

                resolve(data)
            }).catch(error => {
                reject(error)
            })
        })
    },


    // user logout
    logout({
        commit,
        state
    }) {
        return new Promise((resolve, reject) => {
            logout(state.token).then(() => {
                commit('SET_TOKEN', '')
                commit('SET_ROLES', [])
                removeToken()
                resetRouter()
                resolve()
            }).catch(error => {
                reject(error)
            })
        })
    },



    // remove token
    resetToken({
        commit
    }) {
        return new Promise(resolve => {
            commit('SET_TOKEN', '')
            commit('SET_ROLES', [])
            removeToken()
            resolve()
        })
    },

    //query all online devices
    queryDevices({
        state
    }) {
        return new Promise((resolve, reject) => {

            queryDevices({
                token: state.token
            }).then(response => {
                const {
                    data
                } = response


                if (!data) {
                    reject('请求设备信息失败')
                }

                resolve(data)
            }).catch(error => {
                reject(error)
            })
        })
    },

    //user send command
    sendCommand({
        state
    }) {
        return new Promise((resolve, reject) => {
            sendCommand({
                token: state.token,
                serial: state.serial,
                command: state.command
            }).then(response => {


                resolve()
            }).catch(error => {
                reject(error)
            })
        })
    },

    //get device history
    deviceHistory({
        state
    }) {
        return new Promise((resolve, reject) => {
            deviceHistory({
                token: state.token,
            }).then(response => {
                const {
                    data
                } = response
                resolve(data)
            }).catch(error => {
                reject(error)
            })
        })
    },

    //get device history detail
    deviceHistoryDetail({
        state
    }) {
        return new Promise((resolve, reject) => {
            deviceHistoryDetail({
                token: state.token,
                id:state.device_history_id
            }).then(response => {
                const {
                    data
                } = response
                resolve(data)
            }).catch(error => {
                reject(error)
            })
        })
    },


    // Dynamically modify permissions
    // changeRoles({
    //     commit,
    //     dispatch
    // }, role) {
    //     return new Promise(async resolve => {
    //         const token = role + '-token'

    //         commit('SET_TOKEN', token)
    //         setToken(token)

    //         const {
    //             roles
    //         } = await dispatch('getInfo')

    //         resetRouter()

    //         // generate accessible routes map based on roles
    //         const accessRoutes = await dispatch('permission/generateRoutes', roles, {
    //             root: true
    //         })

    //         // dynamically add accessible routes
    //         router.addRoutes(accessRoutes)

    //         resolve()
    //     })
    // }
}

export default {
    namespaced: true,
    state,
    mutations,
    actions
}