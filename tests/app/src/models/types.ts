export interface User {
  email?: string;
  id?: string;
  notes?: Note[];
  date_created?: string;
}

export interface Note {
  id?: string;
  name?: string;
  content?: string;
  starred?: boolean;
  author?: User;
  last_updated?: string;
  date_created?: string;
  is_archived?: string;
}
