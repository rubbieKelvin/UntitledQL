<template>
  <p>loading</p>
</template>

<script lang="ts">
import { defineComponent, watch } from "vue";
import useAuth from "../composables/auth";

export default defineComponent({
  emits: ["auth"],
  setup(prop, { emit }) {
    const { user } = useAuth();

    watch(user, () => {
      if (user.value !== null) {
        emit("auth", user.value);
      }
    });

    return { user };
  },
});
</script>
