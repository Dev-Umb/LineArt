const HelloVueApp = {
    data() {
        return {
            message: 'Hello Vue!!'
        }
    }
}

Vue.createApp(HelloVueApp).mount('#hello-vue')
