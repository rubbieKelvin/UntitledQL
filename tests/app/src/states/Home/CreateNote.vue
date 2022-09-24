<template>
  <div>
    <input type="text" v-model="text" @keypress.enter="submit" />
    <button @click="submit">Create</button>
    <p v-if="error" style="color: red">{{ error }}</p>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref } from "vue";
import { authHeader } from "../../composables/auth";
import { Note } from "../../models/types";
import { uql } from "../../uql/uqlclient";

export default defineComponent({
  props: {
    user: {
      type: Object,
      required: true,
    },
  },
  emits: ["created"],
  setup(props, { emit }) {
    const text = ref("");
    const error = ref("");

    async function submit() {
      if (!text.value.trim()) {
        error.value = "enter a value in text";
        return;
      }

      error.value = "";
      const response = await uql({
        intent: "models.note.insert",
        headers: authHeader(),
        args: {
          object: {
            author: props.user.id,
            name: text.value,
          },
        },
        fields: {
          id: true,
          name: true,
          starred: true,
          author: {
            id: true,
          },
          last_updated: true,
          date_created: true,
          is_archived: true,
        },
      });

      if (response.meta.has_error) {
        error.value = `error creating note; ${response.error?.message}`;
        return;
      }

      text.value = "";
      emit("created", response.data as Note);
    }

    return { text, submit, error };
  },
});
</script>
