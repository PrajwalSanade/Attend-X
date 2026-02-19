import { createClient } from "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm";

const supabaseUrl = "https://wmcviykvnzmmaikunvmf.supabase.co";
const supabaseKey = "sb_publishable_pOG_ctG7m9lFwYZbGYY4bg_T9ycUHiN";

export const supabase = createClient(supabaseUrl, supabaseKey);
