<template>
  <div v-if="user">
    <!-- profile -->
    <div>
      logged in as <b>{{ user.email }}</b>
    </div>

    <!-- create note -->
    <CreateNote :user="user" @created="appendNote" />
    <!-- list notes -->
    <div>
      <NoteItem
        v-for="note in notes"
        :note="note"
        :key="note.id"
        @open="selectedNote = note"
        @update="updateNote"
      />
    </div>
    <!-- edit note -->
    <div v-if="selectedNote">
      <div>
        <hr />
        <h2>{{ selectedNote.name }}</h2>
        <button @click="selectedNote = null">cancel</button>
      </div>
      <textarea v-model="content" cols="30" rows="10" />
      <button @click="saveNoteContent">save</button>
    </div>
    <p v-if="message">{{ message }}</p>
  </div>
</template>

<script lang="ts">
import { defineComponent, onMounted, Ref, ref, watch } from "vue";
import useAuth, { authHeader } from "../../composables/auth";
import { Note } from "../../models/types";
import { uql } from "../../uql/uqlclient";
import CreateNote from "./CreateNote.vue";
import NoteItem from "./NoteItem.vue";

export default defineComponent({
  components: { CreateNote, NoteItem },
  setup() {
    const { user } = useAuth();
    const notes: Ref<Note[]> = ref([]);
    const selectedNote: Ref<Note | null> = ref(null);
    const content = ref("");
    const message = ref("");

    watch(selectedNote, () => {
      message.value = "";
      if (selectedNote.value) content.value = selectedNote.value.content || "";
      else content.value = "";
    });

    onMounted(async () => {
      const response = await uql({
        id: "notes_fetch",
        intent: "models.note.selectmany",
        headers: authHeader(),
        useOfflineFallback: true,
        fields: {
          id: true,
          name: true,
          starred: true,
          content: true,
          author: {
            id: true,
          },
          last_updated: true,
          date_created: true,
          is_archived: true,
        },
      });

      if (!response.meta.has_error) {
        notes.value = response.data;
      }
    });

    function appendNote(note: Note) {
      // reactive update
      notes.value.push(note);
      selectedNote.value = note;
    }

    function updateNote(note: Note) {
      const index = notes.value.findIndex((n) => n.id === note.id);
      if (index === -1) return;
      notes.value[index] = note;
    }

    async function saveNoteContent() {
      const note = selectedNote.value;
      const text = content.value;

      if (!note || note.content === text) {
        message.value = "no changes";
        return;
      }

      const response = await uql({
        intent: "models.note.update",
        headers: authHeader(),
        args: {
          pk: note.id,
          set: {
            content: text.trim(),
          },
        },
      });

      if (response.meta.has_error) {
        message.value = "error saving note";
        return;
      }

      message.value = "note saved";
      const _note = notes.value.find((n) => n.id === note.id);
      if (_note) _note.content = text;
    }

    return {
      user,
      appendNote,
      notes,
      updateNote,
      selectedNote,
      content,
      message,
      saveNoteContent,
    };
  },
});
</script>
