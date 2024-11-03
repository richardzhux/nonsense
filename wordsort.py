# Multiline string input
input_text = """
- Ineffable: indescribable
- Pious
- Behold
- Epiphany
- Servile
- Sinister
- Indignation
- Contemptible
- Befoul
- Complicity
- Absolve
- Solipsism
- Blandishments
- Infidel
- Ostensible
- Ostentatious
- Squirm
- Contortion
- Conclave
- Revulsion
- Desecration
- Exaltation
- Evangelical
- Sterner
- Pretext
- Discernment
- Pomegranate
- Messianic
- Surreptitious
- Apostate
- Apostle
- Ayatollah
- Blasphemy
- Jubilation
- Vouchsafed
- Cadets
- Proselytize
- Reconjure: bring something back as if by magic
- Bigot
- Encephalitic
- Porcophilia/Porcophobia
- Delinquent
- Charcuterie
- Vandalism
- Celibacy
- Promiscuous
- Debauchery
- Bigotry
- Credulous
- Edifice
- Acolyte
- Discrepant
- Inexplicable
- Serf
- Firmament
- Conceit
- Supercilious
- Consummation
- Propensity
- Quintessence
- Filicide
- Puerile
- Underhanded
- Superfluous
- Exuberant
- Teeming
- Inundations
- Inanity
- Conquistador
- Propitiate
- Scrupulous
- Stupendous
- Vicarious
- Inculcate
- Ludicrous
- Leper
- Syphilis Bacillus
- Covenant
- Mutinous
- Impetuous
- Veracity
- Skein
- Megalomania
- Meek
- Demented
- Lasciviousness
- Lapidary
- Premonition
- Palpably
- Apocryphal
- Schismatic
- Sect
- Homoeroticism
- Sadomasochistic
- Farrago
- Deicide
- Onerous
- Disciple
- Ghastly
- Emanation
- Pedantically
- Incandescent
- Hypnotically
- Bewilder
- Immaculate
- Innocuous
- Canonical
- Asinine
- Atrocious
- Ecstatic
- Adumbrated
- Tatter
- Monoglot
- Hadith
- Adjudicate
- Profundity (NO"O"!)
- Satanic
- Thesaurus
- Lucidity
- Tawdriness
- Palladium
- Comeuppance
- Braggart
- Seances
- Riposte
- Corroboration
- Monsignor
- Deacon
- Abdomen
- Superintendent
- Gynecologist
- Affliction
- Shoddy
- Omnipotent/Omniscient/Omnipresent
- Pygmy
- Dissident
- Prescient
- Infallibility
- Unquenchable
- Perilous
- Centaur
- Usher
- Grotesquely
- Hucksterism
- Hectic
- Cupidity
- Scrawny
- Trove
- Disemboweled
- Ecumenical
- Vestigial
- Sinecure
- Sagacious
- Repentance
- Anagram
- Syncretic
- Sermonizer
- Polemic
- Brusquely
- Ruminate
- Eschew
- Devout
- Preach
- Requisite
- Ransom
- Postmortem
- Intransigence
- Conscientious
- Mutilation
- Insistence
- Wrought
- Unbridled
- Insinuation
- Atavistic
- Spasm
- Bloodletting
- Barring
- Atonement
- Meticulous
- Scapegoat
- Dread
- Procreative
- Grotesque
- Genitalia
- Primeval
- Provocation
- Inculcation
- Prophylaxis
- Disfigurement
- Syphilitic
- Stultify
- Onanism
- Protract
- Parishes
- Despotism
- Egalitarianism
- Primordial
- Accession
- Capitulation
- Supervene
- Florid
- Czarism
- Concessionaire
- Liturgy
- Enshrine
- Hermetic
- Quadrilateral
- Predicate
- Malevolent
- Ineluctably
- Halacha
- Demagogue
- Riffraff
- Indolent
- Eschatology
- Zeitgeist
- Exerpt from Christopher Hitchens's Book
- God is not Great
- Exerpt from Christopher Hitchens's Book
- God is not Great
"""

words = [line.strip().lstrip('-').strip() for line in input_text.strip().splitlines()]

# Sort the words alphabetically, case-insensitive
words_sorted = sorted(words, key=lambda word: word.lower())
word_counts = {}
for word in words_sorted:
    word_counts[word] = word_counts.get(word, 0) + 1

# Identify any repeated words
repeated_words = [word for word, count in word_counts.items() if count > 1]
# Count non-repeated words
non_repeated_count = sum(1 for count in word_counts.values() if count == 1)

# Output the sorted list in the input format
print("Sorted words:")
for word in words_sorted:
    print(f"- {word}")

# Output any repeated words in the input format, if any
if repeated_words:
    print("\nRepeated words:")
    for word in repeated_words:
        print(f"- {word}")
else:
    print("\nNo repeated words found.")

# Output the count of non-repeated words
print(f"\nAmount of non-repeated words: {non_repeated_count}\n")