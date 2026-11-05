import DoseGate.Template

namespace DoseGate

theorem span_loop_spec {α : Type} (p : α → Bool) : ∀ (l acc : List α),
    (List.span.loop p l acc).1 ++ (List.span.loop p l acc).2 = acc.reverse ++ l
  | [], acc => by simp [List.span.loop]
  | a :: as, acc => by
      unfold List.span.loop
      split
      · rw [span_loop_spec p as (a :: acc)]; simp
      · simp

theorem span_spec {α : Type} (p : α → Bool) (l : List α) : (l.span p).1 ++ (l.span p).2 = l := by
  unfold List.span
  simpa using span_loop_spec p l []

theorem ofName_spec {name : List Char} {f : Field} (h : Field.ofName? name = some f) :
    name = f.name := by
  unfold Field.ofName? at h
  split at h <;> simp at h <;> subst h <;> simp_all [Field.name]

theorem readSlot_spec {cs : List Char} {f : Field} {id after : List Char}
    (h : readSlot? cs = some (f, id, after)) :
    cs = f.name ++ ':' :: id ++ '}' :: '}' :: after := by
  unfold readSlot? at h
  split at h
  · rename_i inside rest hs
    split at h
    · rename_i name id' after' hs2
      split at h
      · rename_i f' hf
        split at h
        · simp only [Option.some.injEq, Prod.mk.injEq] at h
          obtain ⟨rfl, rfl, rfl⟩ := h
          have e1 := span_spec (· != '}') cs
          have e2 := span_spec (· != ':') inside
          rw [hs] at e1
          rw [hs2] at e2
          simp only at e1 e2
          rw [← e1, ← e2, ← ofName_spec hf]
        · simp at h
      · simp at h
    · simp at h
  · simp at h

theorem unparse_append (a b : List Seg) : unparse (a ++ b) = unparse a ++ unparse b := by
  simp [unparse]

theorem unparse_cons (x : Seg) (xs : List Seg) : unparse (x :: xs) = x.unparse ++ unparse xs := by
  simp [unparse]

theorem unparse_flushText (cur : List Char) : unparse (flushText cur) = cur.reverse := by
  unfold flushText
  split <;> simp_all [unparse, Seg.unparse]

theorem flushText_text_mem {cur t : List Char} (h : Seg.text t ∈ flushText cur) :
    t = cur.reverse ∧ cur ≠ [] := by
  unfold flushText at h
  split at h
  · simp at h
  · rename_i hc
    simp only [List.mem_singleton, Seg.text.injEq] at h
    subst h
    exact ⟨rfl, fun h' => hc (by simp [h'])⟩

theorem parseAux_unparse : ∀ (fuel : Nat) (s cur : List Char) (segs : List Seg),
    parseAux fuel s cur = some segs → unparse segs = cur.reverse ++ s := by
  intro fuel
  induction fuel with
  | zero => intro s cur segs h; simp [parseAux] at h
  | succ n ih =>
    intro s cur segs h
    rcases s with _ | ⟨c, cs⟩
    · simp only [parseAux, Option.some.injEq] at h
      subst h
      simp [unparse_flushText]
    · by_cases hc : c = '{'
      · subst hc
        rcases cs with _ | ⟨d, rest⟩
        · simp [parseAux] at h
        · by_cases hd : d = '{'
          · subst hd
            simp only [parseAux] at h
            split at h
            · rename_i f id after hr
              cases hp : parseAux n after [] with
              | none => simp [hp] at h
              | some segs' =>
                simp only [hp, Option.map_some, Option.some.injEq] at h
                subst h
                have ih' := ih after [] segs' hp
                have hr' := readSlot_spec hr
                rw [unparse_append, unparse_cons, unparse_flushText, ih', hr']
                simp [Seg.unparse, List.append_assoc]
            · simp at h
          · simp [parseAux, hd] at h
      · by_cases hc' : c = '}'
        · subst hc'
          simp [parseAux] at h
        · simp [parseAux, hc] at h
          rw [ih cs (c :: cur) segs h]
          simp [List.reverse_cons, List.append_assoc]

theorem parseAux_text_clean : ∀ (fuel : Nat) (s cur : List Char) (segs : List Seg),
    parseAux fuel s cur = some segs → (∀ c ∈ cur, c ≠ '{' ∧ c ≠ '}') →
    ∀ t, Seg.text t ∈ segs → t ≠ [] ∧ '{' ∉ t ∧ '}' ∉ t := by
  intro fuel
  induction fuel with
  | zero => intro s cur segs h; simp [parseAux] at h
  | succ n ih =>
    intro s cur segs h hcur t ht
    rcases s with _ | ⟨c, cs⟩
    · simp only [parseAux, Option.some.injEq] at h
      subst h
      obtain ⟨rfl, hne⟩ := flushText_text_mem ht
      refine ⟨by simpa using hne, ?_, ?_⟩ <;> intro hm <;> simp only [List.mem_reverse] at hm
      · exact (hcur _ hm).1 rfl
      · exact (hcur _ hm).2 rfl
    · by_cases hc : c = '{'
      · subst hc
        rcases cs with _ | ⟨d, rest⟩
        · simp [parseAux] at h
        · by_cases hd : d = '{'
          · subst hd
            simp only [parseAux] at h
            split at h
            · rename_i f id after hr
              cases hp : parseAux n after [] with
              | none => simp [hp] at h
              | some segs' =>
                simp only [hp, Option.map_some, Option.some.injEq] at h
                subst h
                rcases List.mem_append.mp ht with ht1 | ht2
                · obtain ⟨rfl, hne⟩ := flushText_text_mem ht1
                  refine ⟨by simpa using hne, ?_, ?_⟩ <;> intro hm <;> simp only [List.mem_reverse] at hm
                  · exact (hcur _ hm).1 rfl
                  · exact (hcur _ hm).2 rfl
                · rcases List.mem_cons.mp ht2 with ht3 | ht3
                  · simp at ht3
                  · exact ih after [] segs' hp (by simp) t ht3
            · simp at h
          · simp [parseAux, hd] at h
      · by_cases hc' : c = '}'
        · subst hc'
          simp [parseAux] at h
        · simp [parseAux, hc] at h
          exact ih cs (c :: cur) segs h (by
            intro x hx
            rcases List.mem_cons.mp hx with rfl | hx
            · exact ⟨hc, hc'⟩
            · exact hcur x hx) t ht

theorem unparse_parseTemplate {s : List Char} {segs : List Seg} (h : parseTemplate s = some segs) :
    unparse segs = s := by
  have := parseAux_unparse _ s [] segs h
  simpa using this

theorem parseTemplate_text_no_braces {s t : List Char} {segs : List Seg}
    (h : parseTemplate s = some segs) (ht : Seg.text t ∈ segs) : '{' ∉ t ∧ '}' ∉ t := by
  have := parseAux_text_clean _ s [] segs h (by simp) t ht
  exact ⟨this.2.1, this.2.2⟩

theorem parseTemplate_text_nonempty {s t : List Char} {segs : List Seg}
    (h : parseTemplate s = some segs) (ht : Seg.text t ∈ segs) : t ≠ [] := by
  have := parseAux_text_clean _ s [] segs h (by simp) t ht
  exact this.1

end DoseGate
