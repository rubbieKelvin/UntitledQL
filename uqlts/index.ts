import { Axios } from "axios";

export const UQLClient = (url: string) => {
  const _axios = new Axios({
    url,
    timeout: 10000,
  });

  return () => {
    return {
      _axios,
      call: async (
        intent: string,
        args: Record<string, any>,
        fields: boolean | Record<string, any> | null = null,
        formdata: FormData | null = null,
        headers: Record<string, string> | null = null
      ) => {
        // prepare body
        const body = formdata ?? new FormData();
        body.append(
          "__uql.request.body",
          JSON.stringify({ intent, args, fields })
        );

        // send request
        const response = await _axios.request({
          method: "post",
          data: body,
          headers: {
            ...(headers ?? {}),
          },
        });

        return response;
      },
      subscribe() {},
    };
  };
};
