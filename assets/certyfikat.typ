#let data = sys.inputs 
#let tr = json.decode(data.training)
#let participants = json.decode(data.participants)

#set page(paper: "a4", margin: 2cm)
#set text(font: "DejaVu Sans", size: 12pt, lang: "pl")

#let primary-color = rgb("#7B9FF3")

// Helper for the blue decorative lines
#let blue-line = line(length: 100%, stroke: 1.5pt + primary-color)

// Helper to format the Tematyka list on Page 2
#let format-list(txt) = {
  let lines = txt.split("\n").filter(it => it.trim() != "")
  enum(..lines.map(l => l.replace(regex("^\d+\.\s*"), "")))
}

#for (i, p) in participants.enumerate() {
  // --- PAGE 1: FRONT ---
  
  // Absolute elements (Logo, Stamp, ID)
  place(top + left, image("logo.png", width: 6.2cm), dx: -0.5cm, dy: 0cm)
  place(top + right, image("stamp.png", width: 7.5cm), dx: 0.5cm, dy: 0.4cm)
  
  // UUID / Certificate Number
  place(top + left, text(9pt, [#tr.numer_szkolenia/#(i + 1)]), dy: 3.5cm)

  // Main Content Stack
  move(dy: 4cm)[
    #stack(
      dir: ttb,
      spacing: 1.2em,
      
      blue-line,
      v(0.5cm),
      align(center, text(22pt, weight: "bold")[ZAŚWIADCZENIE]),
      align(center, text(12pt)[O UKOŃCZENIU FORMY DOSKONALENIA ZAWODOWEGO]),
      v(0.5cm),
      blue-line,
      
      v(1.5cm),
      align(center)[Pan/i],
      align(center, text(20pt, weight: "bold")[#p.imie_nazwisko]),
      
      v(1cm),
      align(center)[
        urodzony/a: #p.data_urodzenia, #p.miejsce_urodzenia \
        #v(1.5cm)
        ukończył/a szkolenie:
      ],
      
      align(center, text(18pt, style: "italic")[„#tr.nazwa_szkolenia”]),
      
      v(2cm),
      grid(
        columns: (1fr, 1fr),
        align: center,
        [w dniu: #tr.data_szkolenia],
        [w wymiarze: #tr.czas_trwania]
      ),
      
      v(1.5cm),
      align(center)[
        zorganizowane przez Niepubliczną Placówkę Doskonalenia Nauczycieli \
        Best Practice Edukacja w Wieliczce
      ],
    )
  ]

  // Footer Info
  place(bottom + left, dy: -3cm)[
    Zaświadczenie wydano: \
    Wieliczka, #tr.data_wystawienia r.
  ]

  pagebreak()

  // --- PAGE 2: BACK (Plan szkolenia) ---
  
  // Re-place logo for branding on back
  align(right, image("logo.png", width: 4cm))
  
  v(1cm)
  [== Plan szkolenia:]
  v(0.5cm)
  
  table(
    columns: (1fr),
    inset: 10pt,
    align: horizon,
    fill: luma(250),
    [*Tematyka*],
    format-list(tr.tematyka)
  )

  // Avoid a blank page after the last participant
  if i < participants.len() - 1 {
    pagebreak()
  }
}
