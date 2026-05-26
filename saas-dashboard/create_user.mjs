import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  'https://muhznvrdafzodjmknskc.supabase.co',
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im11aHpudnJkYWZ6b2RqbWtuc2tjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzg5NDg5NTUsImV4cCI6MjA5NDUyNDk1NX0.cs-WJC3FT9Shj_Eo3wpa4N3EjpEP0hT8qPQQ7mmjyBs'
);

async function main() {
  console.log("Checking login...");
  const { data: loginData, error: loginError } = await supabase.auth.signInWithPassword({
    email: 'ashiksiddike@gmail.com',
    password: 'ashik11996786',
  });

  if (loginError) {
    console.log("Login Error:", loginError.message);
  } else if (loginData.session) {
    console.log("User already exists and login works!");
    return;
  }

  console.log("Creating user...");
  const { data, error } = await supabase.auth.signUp({
    email: 'ashiksiddike@gmail.com',
    password: 'ashik11996786',
  });
  console.log("Sign up result:", JSON.stringify({data, error}, null, 2));
}

main();
