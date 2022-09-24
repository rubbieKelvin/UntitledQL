<template>
  <div>
    <span>Signup</span>
    <div v-if="error">{{ error }}</div>
    <div>
      <p>Email</p>
      <input type="email" v-model="data.email" />
    </div>
    <div>
      <p>Password</p>
      <input type="password" v-model="data.password" />
    </div>
    <div>
      <button @click="signup">Signup</button>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, Ref, ref } from "vue";
import useAuth from "../composables/auth";

export default defineComponent({
  emits: ["success", "error"],
  setup(prop, ctx) {
    const auth = useAuth();
    const data = ref({ email: "", password: "" });
    const error: Ref<string | null> = ref(null);
    const signup = async () => {
      const _data = data.value;
      const result = await auth.signup(_data.email, _data.password);

      //   clear
      if (!result.meta.has_error) {
        data.value.email = "";
        data.value.password = "";
        error.value = null;
        ctx.emit("success", result.data);
        return;
      }

      error.value = result.error?.message || "Error occured";
      ctx.emit("error");
    };
    return { data, signup, error };
  },
});
</script>
