<template>
  <div class="flex gap-2 mt-1">
    <button @click="starred = !starred">
      {{ starred ? "starred" : "not starred" }}
    </button>
    <p @click="$emit('open', note)" class="cursor-default">{{ note.name }}</p>
  </div>
</template>

<script lang="ts">
import { computed, defineComponent } from "vue";
import { authHeader } from "../../composables/auth";
import { Note } from "../../models/types";
import { uql } from "../../uql/uqlclient";

export default defineComponent({
  props: { note: { type: Object as () => Note, required: true } },
  emits: ["update", "open"],
  setup(prop, { emit }) {
    const starred = computed({
      get() {
        const note = prop.note as Note;
        return note.starred;
      },
      async set(value) {
        const note = prop.note as Note;
        const response = await uql({
          intent: "models.note.update",
          headers: authHeader(),
          args: {
            pk: note.id,
            set: {
              starred: value,
            },
          },
        });

        if (!response.meta.has_error) {
          emit("update", { ...note, starred: value });
        }
      },
    });

    return { starred };
  },
});
</script>
