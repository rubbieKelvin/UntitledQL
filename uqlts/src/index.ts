import { Axios } from "axios";

const UQLClient = (url: string) => {
  const _axios = new Axios({
    baseURL: url,
    timeout: 10000,
  });

  return {
    call: async (
      intent: string,
      args: Record<string, any> | null = null,
      fields: boolean | Record<string, any> | null = null,
      formdata: FormData | null = null,
      headers: Record<string, string> | null = null
    ) => {
      // prepare body
      const body = formdata ?? new FormData();

      body.append(
        "$uql.request.body",
        JSON.stringify({ intent, args, fields })
      );

      // send request
      const response = await _axios.request({
        method: "post",
        data: body,
        headers: {
          ...(headers ?? {}),
          "Content-Type": "multipart/form-data",
        },
      });

      return response;
    },
    subscribe() {},
  };
};

UQLClient("");
