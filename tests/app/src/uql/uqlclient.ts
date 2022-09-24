export type UQLCallInput = {
  id?: string;
  headers?: Record<string, string>;
  intent: string;
  args?: Object;
  fields?: "$all" | Object | null;
  useOfflineFallback?: boolean;
};

export type UQLCallOutput = {
  meta: {
    has_error: boolean;
    status_code: number;
    // client custom types
    network: "offline" | "online"; // specify how the data was gotten
  };
  data: any;
  error: {
    code: null | number;
    type: string | null;
    message: string | null;
  } | null;
  warning: null | string;
};

const _readResponse = (
  id?: string
): UQLCallOutput | null | Record<string, UQLCallOutput> => {
  const uqlcache = JSON.parse(sessionStorage.getItem("uql") || "{}");
  if (id) {
    return uqlcache[id] || null;
  }
  return uqlcache;
};

const _writeResponse = (id: string, data?: UQLCallOutput) => {
  const uqlcache = _readResponse() as Record<string, UQLCallOutput>;
  if (data) uqlcache[id] = data;
  else delete uqlcache[id];
  sessionStorage.setItem("uql", JSON.stringify(uqlcache));
};

export const uql = async ({
  id,
  intent,
  args,
  fields,
  headers,
  useOfflineFallback,
}: UQLCallInput): Promise<UQLCallOutput> => {
  const root = import.meta.env.VITE_UQL_ROOT;

  try {
    const response = await fetch(root, {
      method: "post",
      headers: new Headers({ "Content-Type": "application/json", ...headers }),
      body: JSON.stringify({
        intent,
        args,
        fields,
      }),
    });
    const json = (await response.json()) as UQLCallOutput;
    json.meta["network"] = "online";

    if (id) {
      _writeResponse(id, json);
    }

    return json;
  } catch (e) {
    if (useOfflineFallback) {
      console.assert(
        !!id,
        "id should not be null when useOfflineFallback is true"
      );
      console.assert(
        /(^models.\w+\.find$)|(^models.\w+\.selectmany$)/.test(intent),
        "Only use useOfflineFallback=true when selecting models"
      );

      const res = _readResponse(id) as UQLCallOutput | null;
      if (res) {
        res.meta.network = "offline";
        return res;
      }
    }

    return {
      meta: {
        has_error: true,
        status_code: -1,
        network: "offline",
      },
      data: null,
      error: {
        code: -1,
        type: "Network error",
        message: `${e}`,
      },
      warning: null,
    };
  }
};
