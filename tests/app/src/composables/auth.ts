import { computed, onMounted, Ref, ref } from "vue";
import { User } from "../models/types";
import { uql, UQLCallOutput } from "../uql/uqlclient";

export interface SignupResponse extends UQLCallOutput {
  data: {
    user: User;
    token: string;
  } | null;
}

export interface UserModelResponse extends UQLCallOutput {
  data: User;
}

export const authToken = (): string | null => localStorage.getItem("xt");
export const authHeader = (): { Authorization: string } => {
  const token = authToken();
  if (token) return { Authorization: `Token ${token}` };
  throw new Error("token no found");
};

export default () => {
  const user: Ref<User | null | false> = ref(null);

  // methods
  const signup = async (
    email: string,
    password: string
  ): Promise<SignupResponse> => {
    const result = (await uql({
      intent: "functions.signup",
      args: { email, password },
      fields: {
        user: {
          email: true,
          id: true,
        },
        token: true,
      },
    })) as SignupResponse;

    // store
    if (!result.meta.has_error && result.data?.token) {
      localStorage.setItem("xt", result.data?.token);
    }
    return result;
  };
  const login = () => {};
  const logout = () => {};

  onMounted(async () => {
    const token = authToken();

    if (token) {
      // has token
      const res = (await uql({
        id: "auth_user",
        intent: "models.user.find",
        useOfflineFallback: true,
        headers: { Authorization: `Token ${token}` },
        args: {
          where: {
            is_active: {
              _eq: true,
            },
          },
        },
        fields: {
          email: true,
          id: true,
          date_created: true,
        },
      })) as UserModelResponse;

      if (!res.meta.has_error) {
        user.value = res.data;
      } else {
        user.value = false;
      }
    } else {
      user.value = false;
    }
  });

  return { signup, login, logout, user };
};
