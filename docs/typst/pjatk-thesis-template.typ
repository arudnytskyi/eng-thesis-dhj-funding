#let title-page-layout(
  logo-path: "",
  faculty: "",
  department: "",
  specialization: "",
  title: "",
  thesis-type: "",
  author-info: (:), // expects (name: "", id: "")
  supervisor-info: (:), // expects (label: "", name: "")
  location-info: "", // "Warsaw, Month, Year"
) = {
  // Define relative spacing
  let gap-xl = 1fr
  let gap-lg = 0.7fr
  let gap-md = 0.32fr
  let gap-sm = 0.12fr

  set align(center)
  show title: set text(size: 14pt)

  // Logo
  if logo-path != "" {
    image(logo-path, width: 125mm, alt: "PJATK Logo")
  } else {
    v(3cm)
    text(weight: "bold", size: 16pt)[PJATK]
  }

  v(gap-lg)

  // Faculty Info
  strong(faculty)
  v(gap-md)
  strong(department)
  v(gap-sm)
  specialization

  v(gap-lg)

  // Author Info
  strong(author-info.name)
  v(gap-sm)
  author-info.id

  v(gap-lg)

  // Thesis Title
  text(weight: "bold", title)

  v(gap-xl)

  // Supervisor (Aligned Right)
  align(end)[
    #box()[
        #align(start)[
        #thesis-type \
        #strong(supervisor-info.label) \
        #supervisor-info.name
      ]
    ]
  ]

  v(gap-xl)

  // Date
  location-info
  
  pagebreak()
}

#let abstract-page-layout(
  title: "",
  content: [],
  keywords-label: "",
  keywords: ""
) = {
  block(below: 1em, text(weight: "bold", size: 14pt, title))
  content
  v(1em)
  block(below: 0.5em, text(weight: "bold", size: 12pt, keywords-label))
  keywords
  pagebreak()
}

#let thesis(
  // 1. Information Groups (Dictionaries for cleaner API)
  author: (name: "", id: ""),
  supervisor: (name: ""),
  
  // 2. Thesis Metadata
  thesis: (
    title-en: "",
    title-pl: "",
    type-en: "Engineering thesis",
    type-pl: "Praca inżynierska",
  ),

  // 3. Faculty / Department Config
  faculty: (
    en: "Faculty of Information Technology",
    pl: "Wydział Informatyki",
    dept-en: "Department of Intelligent Systems and Data Science",
    dept-pl: "Katedra Systemów Inteligentnych i Data Science",
    spec-en: "Specialization Intelligent data processing systems",
    spec-pl: "Specjalizacja Inteligentne systemy przetwarzania danych",
  ),

  // 4. Abstracts
  abstracts: (
    en: [],
    pl: [],
    keywords-en: "",
    keywords-pl: "",
  ),

  // 5. Assets
  logos: (
    en: "",
    pl: "",
  ),

  bib-file: "",
  source-code: "",

  // 6. Content
  body
) = {
  
  // --- Global Settings ---
  set page(
    paper: "a4",
    margin: 2.5cm,
  )

  set text(
    font: "Times New Roman",
    size: 12pt,
    lang: "en",
    region: "gb"
  )

  set par(
    justify: true, 
    leading: 0.65em
  )

  // --- Heading Styling ---
  set heading(numbering: "1.1.")
  show heading: it => {
    set text(font: "Times New Roman", weight: "bold")
    set block(above: 2em, below: 1em)
    if it.level == 1 {
      text(size: 14pt, it)
    } else {
      text(size: 12pt, it)
    }
  }

  show raw.where(block: false): box.with(
    fill: luma(240),
    inset: (x: 3pt, y: 0pt),
    outset: (y: 3pt),
    radius: 2pt,
  )

  show footnote.entry: set text(size: 10pt)

  // --- Date Calculation ---
  let date-en = "Warsaw, " + datetime.today().display("[month repr:long], [year]")
  let date-pl = "Warszawa, " + datetime.today().display("[month repr:long], [year]")

  // --- Generate English Title Page ---
  title-page-layout(
    logo-path: logos.en,
    faculty: faculty.en,
    department: faculty.dept-en,
    specialization: faculty.spec-en,
    title: thesis.title-en,
    thesis-type: thesis.type-en,
    author-info: author,
    supervisor-info: (label: "Supervisor:", name: supervisor.name),
    location-info: date-en
  )

  // --- Generate Polish Title Page ---
  title-page-layout(
    logo-path: logos.pl,
    faculty: faculty.pl,
    department: faculty.dept-pl,
    specialization: faculty.spec-pl,
    title: thesis.title-pl,
    thesis-type: thesis.type-pl,
    author-info: author,
    supervisor-info: (label: "Promotor:", name: supervisor.name),
    location-info: date-pl
  )

  // --- Abstracts ---
  set page(numbering: "1")

  abstract-page-layout(
    title: "Abstract",
    content: abstracts.en,
    keywords-label: "Keywords",
    keywords: abstracts.keywords-en
  )

  abstract-page-layout(
    title: "Abstrakt", // [cite: 161]
    content: abstracts.pl,
    keywords-label: "Słowa kluczowe",
    keywords: abstracts.keywords-pl
  )

  // --- Table of Contents ---
  outline(title: "Content") 
  pagebreak()

  // --- Main Body ---
  body

  // --- Lists ---
  pagebreak()
  heading(level: 1, numbering: none)[Lists]
  outline(title: "List of Tables", target: figure.where(kind: table))
  v(1em)
  outline(title: "List of Figures", target: figure.where(kind: image))
  

  if bib-file != none {
    pagebreak()
    bibliography(bib-file, style: "chicago-notes") 
  }

  if source-code != none {
    pagebreak()
    set heading(numbering: none)
    heading(level: 1, numbering: none)[Appendix A: Source Code Repository]
    text("The source code developed and used for experiments described in this thesis is available at: ")
    link(source-code)[#source-code]
  }
}