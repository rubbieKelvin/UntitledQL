<template>
  <div>
    <Init v-if="currentState === 'init'" @auth="onLoad" />
    <Signup
      v-if="currentState === navigationStates.SIGNUP"
      @success="currentState = 'home'"
    />
    <Home v-else-if="currentState === navigationStates.HOME" />
  </div>
</template>

<script lang="ts">
import { defineComponent, provide } from "vue";
import useNavigation, { navigationStates, STATE } from "./composables/navigation";
import Signup from "./states/Signup.vue";
import Home from "./states/Home/index.vue";
import Init from "./states/Init.vue";
import { User } from "./models/types";

export default defineComponent({
  components: { Signup, Home, Init },
  setup() {
    const navigation = useNavigation();

    provide('navigation', {
      state: navigation.state,
      updateState(value: STATE){
        navigation.state.value = value
      }
    })

    function onLoad(data: User | false) {
      if (data) {
        navigation.state.value = "home";
      } else {
        navigation.state.value = "signup";
      }
    }
    return { currentState: navigation.state, navigationStates, onLoad };
  },
});
</script>
