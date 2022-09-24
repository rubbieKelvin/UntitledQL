import { Ref, ref } from "vue";

export type STATE = "init" | "signup" | "login" | "home";

export const navigationStates: Record<string, STATE> = {
  SIGNUP: "signup",
  LOGIN: "login",
  HOME: "home",
};

export default () => {
  const state: Ref<STATE> = ref("init");
  return { state };
};
