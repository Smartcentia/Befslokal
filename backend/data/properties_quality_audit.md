# Eiendomskvalitet – revisjon (Bufdir, navn/adresse, geodata, duplikater)

_Generert: 2026-04-07 22:39 UTC_

## Sammendrag

- Totalt eiendommer: **636**
- Minst ett avvik: **201**

- `address_differs_from_bufdir_json`: **48**
- `bufdir_cache_name_differs_from_json`: **1**
- `duplicate_property_name`: **31**
- `missing_accounting_linkage`: **111**
- `missing_geolocation`: **33**
- `missing_street_address_only`: **11**
- `name_looks_like_address`: **29**
- `property_name_differs_from_bufdir_official`: **16**

---

## address_differs_from_bufdir_json

| property_id | Navn (kort) | Adresse | Merknad |
|---|---|---|---|
| `a89161b1-12a6-4c23-bfd6-8bc127bf60ed` | Vikhovlia akuttsenter | Vikhovlia 1400 | Bufdir JSON-adresse: Besøksadresse: Vikhovlia 1400, 7560 Vikhammer \n Postadresse: Postboks 2233, 3103 Tønsberg |
| `2a5e1655-696e-454e-ae68-fee47101a6ec` | Jong ungdoms- og familiesenter, Åsen | Emma Hjortsvei 60 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Bufdir JSON-adresse: Postadresse : Postboks 2233, 3103 Tønsberg |
| `a2d3ee33-f2e4-4525-8d47-925fbfe4d821` | Østfold ungdoms- og familiesenter, Alfheim | Alfheimvn 6 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Bufdir JSON-adresse: Postadresse : Postboks 2233, 3103 Tønsberg |
| `b2713a9e-0aef-472a-a921-fa4844d960bb` | Karienborg ungdomsheim | Okkenhaugveien 13B | Bufdir JSON-adresse: \n Besøksadresse: Okkenhaugveien 13B, Levanger \n \n Postadresse: Postboks 2233, 3103 Tønsberg |
| `e3a5849c-29f7-4261-ae71-d7fde1ae2bef` | Ringerike omsorgssenter for barn | Åsaveien 662 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Bufdir JSON-adresse: Postadresse : Postboks 2233, 3103 Tønsberg |
| `df67f736-1ccd-4fb1-b689-023f1a177132` | Kvæfjord Ungdomssenter | Heimlyvn 5 | Bufdir JSON-adresse: Besøksadresse Bregnetunet 15, 6812 Førde \n Postadresse Postboks 2233, 3103 Tønsberg |
| `3ca20ffa-667b-40e5-abac-9366b80c6400` | Bjørgvin Ungdomssenter, avd. Bønesskogen | Bønesskogen 333 | Bufdir JSON-adresse: Besøksadresse Bønesskogen 333, 5154 Bønes \n Postadresse Postboks 2233 3103 Tønsberg |
| `b3a93c6a-50d1-46e5-bce5-05a06b46eedf` | Kollen ungdomsbase, Vestnes | Myrakollen | Bufdir JSON-adresse: Besøksadresse: Myrakollen 2 - 16, Vestnes \n Postadresse: Postboks 2233, 3103 Tønsberg |
| `7ffb1d6c-5155-47ce-93b3-0c9d70c10de3` | Lunde behandlingssenter | Lundeveien 171 | Bufdir JSON-adresse: $33 |
| `86f949d8-c05c-490f-baf7-2700432acc5e` | Akershus ungdoms- og familiesenter - akutt, avd Bjørlien | Bjørlistubben 14 | Bufdir JSON-adresse: Postadresse : Postboks 2233, 3103 Tønsberg |
| `dbbff592-2fed-4390-bece-8eafbf514226` | Østfold ungdoms- og familiesenter - omsorg, avdeling Kurland | Kurlandveien 12 | Bufdir JSON-adresse: Postadresse : Postboks 2233, 3103 Tønsberg |
| `0b639970-3074-4d2e-a6bd-6af841e840a5` | Bufetats behandlingssenter Akershus_Østfold, avd Ressursteam | Solfallsveien 27 | Bufdir JSON-adresse: Postadresse : Postboks 2233, 3103 Tønsberg |
| `438c4047-1861-47f4-b655-1b8f283f86cc` | Feilregistert | Nedre Nattland 69 | Bufdir JSON-adresse: Besøksadresse Nedre Nattland 69, 5099 Bergen \n Postadresse Postboks 2233, 3103 Tønsberg Eiendomsnavn i DB ligner ikke Bufdir offisielt navn. |
| `b8fcd912-7c52-4294-907c-8ada717c9268` | Skjoldvegen Skjold | Skjoldvegen 51 | Lagret institution_name avviker fra JSON (cache utdatert?). JSON: Fana og Ytrebygda ungdomssenter, Skjold Bufdir JSON-adresse: Besøksadresse Skjoldvegen 51/55, 5221 Nesttun \n Postadresse Postboks 223 |
| `65080457-34c4-4962-8600-ebac380f3bb7` | Yttrabekken Ungdomssenter | Brennstadmoen 23 | Bufdir JSON-adresse: Besøksadresse: Brennstadmoen 23, 8614 Mo i Rana \n Postadresse: Postboks 2233, 3103 Tønsberg |
| `e39e55b9-76ba-4165-a7ff-2cd6cb324143` | Tromsø Ungdomssenter | Håkøyvn 339 | Bufdir JSON-adresse: Besøksadresse: Håkøyvegen 339, 9105 Kvaløya \n Postadresse: Postboks 2233, 3103 Tønsberg |
| `c2e24201-7b61-498e-96b0-225c48c2f8af` | Sollia barne- og ungdomssenter | Idrettsvn 5 | Bufdir JSON-adresse: Besøksadresse: Idrettsveien 5, 8402 Sortland \n Postadresse: Postboks 2233, 3103 Tønsberg |
| `fd0d6ac2-c7ce-4ad6-baed-b74c4cea8482` | Sundstedtråkka | Storgaten 62-64 | Samme navn som 1 annen(e) eiendom: 338600a3-649d-4b0d-9b76-124aaf50771f Bufdir JSON-adresse: Besøksadresse \n Haugsundgata 62, 3303 Hokksund \n Postadresse \n Postboks 2230, 3103 Tønsberg \n Be Eiendo |
| `53181bf2-e205-4486-a30d-0342cc1e1ea6` | Bodø ungdomssentersenter | Skoleveien 9 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Bufdir JSON-adresse: Besøksadresse Rødstokken 16, 6856 Sogndal \n Postadresse Postboks 2233, 3103 Tønsberg |
| `5a70a668-6ab8-4412-befe-6fc93e40b181` | Sunnmørsheimen akuttinstitusjon, avd. Klatrevegen | Klatrevegen 2 | Bufdir JSON-adresse: Besøksadresse: Klatrevegen 2, 6104 Volda \n Postadresse: Postboks 2233, 3103 Tønsberg |
| `776defcb-d174-4332-aa14-1f0081d55911` | Klokkerhuset | Ulefossveien 53 | Samme navn som 1 annen(e) eiendom: 442eeb8d-cc2e-48f2-9f0b-6382d8de0880 Bufdir JSON-adresse: Administrasjon \n Ulefossvegen 52, 3730 Skien \n Klokkerhuset \n Ulefossveien 52, Bygg 27, 3730 Skie |
| `6b4073f1-3a4e-46d4-a3dd-53b99dee678d` | Buvika ungdomssenter | Hanskleiva 25 | Bufdir JSON-adresse: Besøksadresse: \n Bønesstølen 13, 5154 Bønes \n Postadresse: \n Postboks 2233, 3103 Tønsberg |
| `247566b1-58b0-4a81-9fea-40523ecde657` | Øverbyvegen 88 -104 | Tokerudkollen 31-33 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Samme navn som 1 annen(e) eiendom: 33ee9f33-c71b-4f77-bd0e-cbce78cc3eef Bufdir JSON-adresse: Postadresse : Postbo |
| `1d6a85cc-827e-417c-9c4a-b0581c901824` | Jernbanevegen 70 | Jernbaneveien 70 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Bufdir JSON-adresse: Postadresse : Postboks 2233, 3103 Tønsberg Eiendomsnavn i DB ligner ikke Bufdir offisielt na |
| `5faead1e-e83e-4294-b78b-585edc1ba52b` | Veslekila 1 | Veslekila 3A | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Bufdir JSON-adresse: Postadresse : Postboks 2233, 3103 Tønsberg Eiendomsnavn i DB ligner ikke Bufdir offisielt na |
| `555393a1-3efb-4b8a-b179-bbfca9fa61ee` | Nes | Nesverkveien 190 | Bufdir JSON-adresse: Adresse \n Frogs vei 19, 3611 Kongsberg \n Postadresse \n Postboks 2233, 3103 Tønsberg Eiendomsnavn i DB ligner ikke Bufdir offisielt navn. |
| `3dad633d-78cc-477e-8518-3dbdc4448883` | Trondheimsveien 205 | Trondheimsvegen - Jessheim 205 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Bufdir JSON-adresse: Postadresse : Postboks 2233, 3103 Tønsberg Eiendomsnavn i DB ligner ikke Bufdir offisielt na |
| `1679f1b0-cdb7-4a06-a067-4a34e15dc2f4` | Lerketoppen | Grimestadveien 69 | Bufdir JSON-adresse: Besøksadresse: Grimestadveien 69, 3160 Stokke \n Postadresse: Postboks 2233, 3103 Tønsberg Eiendomsnavn i DB ligner ikke Bufdir offisielt navn. |
| `4b3185d4-2cee-40c6-8b40-e9fce684b0de` | Bufetats behandlingssenter Akershus_Østfold, avd Kroerveien | Kroerveien 9 | Bufdir JSON-adresse: Postadresse : Postboks 2233, 3103 Tønsberg |
| `ceaeea8d-0917-44dc-a290-47ecc110b65c` | Hedmark ungdoms- og familiesenter - akutt, avd Disen | Just Brochs gate 13 | Bufdir JSON-adresse: Postadresse : Postboks 2233, 3103 Tønsberg |
| `005ea20f-5be6-40ae-a2bf-28411c16c067` | Akershus ungdoms- og familiesenter, Sole | Njords vei 11 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Bufdir JSON-adresse: Postadresse : Postboks 2233, 3103 Tønsberg |
| `51791f47-6740-43c4-8575-a9dc319b0b4b` | Bufetats behandlingssenter Akershus/Østfold, Østlund | Stasjonsveien 16B | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Bufdir JSON-adresse: Postadresse : Postboks 2233, 3103 Tønsberg |
| `00658fb2-21fd-48d2-a839-cc525e28afe2` | Østfold ungdoms- og familiesenter, Rokkeveien | Rokkeveien 502 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Bufdir JSON-adresse: Postadresse : Postboks 2233, 3103 Tønsberg |
| `ec1c9fc5-fda8-49c6-87a9-5064c304af3b` | Lierfoss ungdoms- og familiesenter, Riserhagen | Riserveien 40A/B | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Bufdir JSON-adresse: Postadresse : Postboks 2233, 3103 Tønsberg |
| `a6e9ab34-7dd0-4afb-8590-44ee473ba6f3` | Kasa Ungdomssenter avd. Flatøy | Flatøyvegen 45 | Bufdir JSON-adresse: Besøksadresse Flatøyvegen 45, 5918 Frekhaug \n Postadresse Postboks 2233, 3103 Tønsberg Postboks 130 |
| `831ea4c5-f627-42aa-9849-b46bbc9e89cf` | Bufetats behandlingssenter Akershus_Østfold, avd Østheim | Østheimveien 14 | Bufdir JSON-adresse: Postadresse : Postboks 2233, 3103 Tønsberg |
| `de02cb91-c790-4edb-a291-d59b50db2016` | Storveien 1404/1408 | Storveien 1404 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Bufdir JSON-adresse: Postadresse : Postboks 2233, 3103 Tønsberg Eiendomsnavn i DB ligner ikke Bufdir offisielt na |
| `c06dc87e-21b6-413d-add9-a09345939cb2` | Ungdomsheimen | Husafjellet 6 | Bufdir JSON-adresse: \n Besøksadresse: Husafjellet 6, 6009 Ålesund \n \n Postadresse: Postboks 2233, 3103 Tønsberg |
| `b9fe4a95-4de1-4cfc-b632-0760886e8505` | Sogn og Fjordane ungdomssenter avdeling Bregnetunet behandli | Bregnetunet 15 | Bufdir JSON-adresse: Besøksadresse Bregnetunet 15, 6812 Førde \n Postadresse Postboks 2233, 3103 Tønsberg |
| `c1d4f513-d858-422d-aacd-237e4083c9dc` | Kasa Ungdomssenter avd. Tertnes | Tertneshøyden 33b | Bufdir JSON-adresse: Besøksadresse Tertneshøyden 33B, 5113 Tertnes \n Postadresse Postboks 2233, 3103 Tønsberg Postboks 3 |
| `d9f6be50-917e-4854-be89-bc3692d90027` | Bjørgvin Ungdomssenter, avd. Bønesstølen | Bønesstølen 13 | Bufdir JSON-adresse: Besøksadresse Bønesstølen 13, 5154 Bønes \n Postadresse Postboks 2233, 3103 Tønsberg |
| `352403aa-d8b5-4855-bc8f-484740d6d678` | Østfold ungdoms- og familiesenter - avdeling Fossen | Skolegata 53 | Bufdir JSON-adresse: Postadresse : Postboks 2233, 3103 Tønsberg |
| `d34979da-4b1f-46d0-96b3-b1266a9f731f` | St. Hansgården | Bispegra 52 | Bufdir JSON-adresse: Besøksadresse \n Bispegra 52, 4632 Kristiansand S \n Postadresse \n Postboks 2233, 3103 Tønsberg |
| `b1205858-6826-447d-a61e-a0bc53cca997` | Clausenengen ungdomshjem | Kvalvågveien 113 | Bufdir JSON-adresse: Besøksadresse: Kvalvågveien 113, 6521 Frei \n Postadresse: Postboks 2233, 3103 Tønsberg |
| `f8edb751-c3c8-41f2-a85f-a4921c5a06e0` | Sunnmørsheimen avd Nygardsvegen | Nygardsvegen 2 og 4 | Bufdir JSON-adresse: Besøksadresse: Nygardsvegen 2 - 4, 6103 Volda \n Postadresse: Postboks 2233, 3103 Tønsberg |
| `60571f11-e626-49b5-9fc1-dd852c4a1fdc` | Orkdal barnevernsenter | Ljåmovein 10 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Bufdir JSON-adresse: \n \n Besøksadresse: Hølondvegen 311, 7223 Melhus \n Postadresse: Postboks 2233, 3103 Tønsbe |
| `42ced846-2ddc-4b9c-b6c5-9fe09a7291fa` | Alta Ungdomssenter | Strandvn 6 | Bufdir JSON-adresse: Besøksadresse \n Lagårdsveien 44, 4010 Stavanger \n \n Postadresse \n Postboks 2233, 3103 Tønsberg |
| `fedc9785-2496-4281-881c-d7101dc2b902` | Østfold ungdoms- og familiesenter, Tune | Vestrevei 1 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Bufdir JSON-adresse: Postadresse : Postboks 2233, 3103 Tønsberg |

## bufdir_cache_name_differs_from_json

| property_id | Navn (kort) | Adresse | Merknad |
|---|---|---|---|
| `b8fcd912-7c52-4294-907c-8ada717c9268` | Skjoldvegen Skjold | Skjoldvegen 51 | Lagret institution_name avviker fra JSON (cache utdatert?). JSON: Fana og Ytrebygda ungdomssenter, Skjold Bufdir JSON-adresse: Besøksadresse Skjoldvegen 51/55, 5221 Nesttun \n Postadresse Postboks 223 |

## duplicate_property_name

| property_id | Navn (kort) | Adresse | Merknad |
|---|---|---|---|
| `07a85e2d-6482-4213-a884-5c70dce8f0a5` | Nordstrand | Nordstrandsveien 49d | Samme navn som 1 annen(e) eiendom: b28a9761-ca75-44fc-a974-d3b74a24a061 |
| `33ee9f33-c71b-4f77-bd0e-cbce78cc3eef` | Øverbyvegen 88 -104 | Øverbyveien 104 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Samme navn som 1 annen(e) eiendom: 247566b1-58b0-4a81-9fea-40523ecde657 Eiendomsnavn i DB ligner ikke Bufdir offi |
| `30bcb03f-45d2-4b07-aa1c-914917e2fcf6` | Bufetathus Haugesund | Haraldsgata 94 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Samme navn som 1 annen(e) eiendom: 9cd8ef03-11f7-4d9f-9543-ee3c5f2a2c8b |
| `fcd55797-687d-4ae4-8f7a-7ad07b0031f2` | Bufetathus Stavanger | Jåttåvågveien 10 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Samme navn som 1 annen(e) eiendom: e4a46d3c-d1a4-4816-8761-db333473e552 |
| `9cd8ef03-11f7-4d9f-9543-ee3c5f2a2c8b` | Bufetathus Haugesund | Rennesøygata 16 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Samme navn som 1 annen(e) eiendom: 30bcb03f-45d2-4b07-aa1c-914917e2fcf6 |
| `88025034-d6a4-4f18-9a75-e132856d867c` | Langenes | Langenesveien 129/131 | Samme navn som 1 annen(e) eiendom: 53169438-154b-4899-92b6-3e722ced5ca6 |
| `ce49e57e-bccd-4359-8805-296cb37158bd` | Miljøheimen | Haugetuft 16-18 | Samme navn som 1 annen(e) eiendom: c0eb5fd0-24c1-4455-ad67-fe8728d8ec8c |
| `08b57672-9f6a-4289-b3cb-6f47ac31f098` | Toppen | Kirkegårsdsveien 25 | Samme navn som 2 annen(e) eiendom: 13ffb54b-6d55-4305-86b3-ea82c9993117, fecd2885-22b7-4a87-a7e3-793863604ce7 |
| `442eeb8d-cc2e-48f2-9f0b-6382d8de0880` | Klokkerhuset | Ulefossveien 52 | Samme navn som 1 annen(e) eiendom: 776defcb-d174-4332-aa14-1f0081d55911 |
| `fd0d6ac2-c7ce-4ad6-baed-b74c4cea8482` | Sundstedtråkka | Storgaten 62-64 | Samme navn som 1 annen(e) eiendom: 338600a3-649d-4b0d-9b76-124aaf50771f Bufdir JSON-adresse: Besøksadresse \n Haugsundgata 62, 3303 Hokksund \n Postadresse \n Postboks 2230, 3103 Tønsberg \n Be Eiendo |
| `776defcb-d174-4332-aa14-1f0081d55911` | Klokkerhuset | Ulefossveien 53 | Samme navn som 1 annen(e) eiendom: 442eeb8d-cc2e-48f2-9f0b-6382d8de0880 Bufdir JSON-adresse: Administrasjon \n Ulefossvegen 52, 3730 Skien \n Klokkerhuset \n Ulefossveien 52, Bygg 27, 3730 Skie |
| `247566b1-58b0-4a81-9fea-40523ecde657` | Øverbyvegen 88 -104 | Tokerudkollen 31-33 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Samme navn som 1 annen(e) eiendom: 33ee9f33-c71b-4f77-bd0e-cbce78cc3eef Bufdir JSON-adresse: Postadresse : Postbo |
| `13ffb54b-6d55-4305-86b3-ea82c9993117` | Toppen | Kirkegårdsveien 25 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Samme navn som 2 annen(e) eiendom: 08b57672-9f6a-4289-b3cb-6f47ac31f098, fecd2885-22b7-4a87-a7e3-793863604ce7 |
| `338600a3-649d-4b0d-9b76-124aaf50771f` | Sundstedtråkka | Storgata 62 | Samme navn som 1 annen(e) eiendom: fd0d6ac2-c7ce-4ad6-baed-b74c4cea8482 |
| `dc937552-4c5a-4cd5-91ea-5641bd32dc12` | FVK, Lofoten og Vesterålen | Nordnesveien 3 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Samme navn som 1 annen(e) eiendom: f9cdf6ff-74e6-45c7-b382-aecd5dea68cd |
| `53169438-154b-4899-92b6-3e722ced5ca6` | Langenes | Langenesveien 129 | Samme navn som 1 annen(e) eiendom: 88025034-d6a4-4f18-9a75-e132856d867c |
| `6645f7f4-c796-4626-88f9-28a979c1ff1c` | Katfoss | Ilaugveien 1 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Samme navn som 1 annen(e) eiendom: da6ccfca-7a22-45ef-b260-3ed9cf7082b1 |
| `1972740e-9933-4490-ac11-353967ff78d5` | Hilde Hasle | Lyderhornslien 73 | Samme navn som 1 annen(e) eiendom: c7cc6337-ea46-49b1-a36a-7c1295524899 |
| `5c82ba87-9138-4096-9307-44f55d50a143` | Hølen | Brandstadveien 96 | Samme navn som 1 annen(e) eiendom: 86fafa26-532c-418a-a743-737bdf99af43 |
| `ac1348ff-a869-4ab6-83d1-c955e561d178` | Thorøya Vaktmesterbolig | Thorøyaveien 1  | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Samme navn som 1 annen(e) eiendom: c9dc5d55-29ff-48f3-a295-5ef0d0bba9fd |
| `f0831c60-192d-4f41-9863-520dbe471caa` | Kantum | Baneveien  19 | Samme navn som 1 annen(e) eiendom: adda3311-6723-4274-8d59-89be53598d59 Eiendomsnavn i DB ligner ikke Bufdir offisielt navn. |
| `86fafa26-532c-418a-a743-737bdf99af43` | Hølen | Gjølstadveien 141 | Samme navn som 1 annen(e) eiendom: 5c82ba87-9138-4096-9307-44f55d50a143 |
| `e4a46d3c-d1a4-4816-8761-db333473e552` | Bufetathus Stavanger | Lagårdsveien 44 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Samme navn som 1 annen(e) eiendom: fcd55797-687d-4ae4-8f7a-7ad07b0031f2 |
| `adda3311-6723-4274-8d59-89be53598d59` | Kantum | Baneveien 19 | Samme navn som 1 annen(e) eiendom: f0831c60-192d-4f41-9863-520dbe471caa |
| `c0eb5fd0-24c1-4455-ad67-fe8728d8ec8c` | Miljøheimen | Haugetuft 16 | Samme navn som 1 annen(e) eiendom: ce49e57e-bccd-4359-8805-296cb37158bd |
| `b28a9761-ca75-44fc-a974-d3b74a24a061` | Nordstrand | Lindbãckveien 53 D | Samme navn som 1 annen(e) eiendom: 07a85e2d-6482-4213-a884-5c70dce8f0a5 |
| `c7cc6337-ea46-49b1-a36a-7c1295524899` | Hilde Hasle | Lyderhornslien 73 | Samme navn som 1 annen(e) eiendom: 1972740e-9933-4490-ac11-353967ff78d5 |
| `c9dc5d55-29ff-48f3-a295-5ef0d0bba9fd` | Thorøya Vaktmesterbolig | Thorøyaveien 1 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Samme navn som 1 annen(e) eiendom: ac1348ff-a869-4ab6-83d1-c955e561d178 |
| `f9cdf6ff-74e6-45c7-b382-aecd5dea68cd` | FVK, Lofoten og Vesterålen | Markedsgt 20 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Samme navn som 1 annen(e) eiendom: dc937552-4c5a-4cd5-91ea-5641bd32dc12 |
| `da6ccfca-7a22-45ef-b260-3ed9cf7082b1` | Katfoss | Ilaugveien 1A | Samme navn som 1 annen(e) eiendom: 6645f7f4-c796-4626-88f9-28a979c1ff1c |
| `fecd2885-22b7-4a87-a7e3-793863604ce7` | Toppen | Toppenvegen 14 | Samme navn som 2 annen(e) eiendom: 08b57672-9f6a-4289-b3cb-6f47ac31f098, 13ffb54b-6d55-4305-86b3-ea82c9993117 |

## missing_accounting_linkage

| property_id | Navn (kort) | Adresse | Merknad |
|---|---|---|---|
| `33ee9f33-c71b-4f77-bd0e-cbce78cc3eef` | Øverbyvegen 88 -104 | Øverbyveien 104 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Samme navn som 1 annen(e) eiendom: 247566b1-58b0-4a81-9fea-40523ecde657 Eiendomsnavn i DB ligner ikke Bufdir offi |
| `2a5e1655-696e-454e-ae68-fee47101a6ec` | Jong ungdoms- og familiesenter, Åsen | Emma Hjortsvei 60 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Bufdir JSON-adresse: Postadresse : Postboks 2233, 3103 Tønsberg |
| `a2d3ee33-f2e4-4525-8d47-925fbfe4d821` | Østfold ungdoms- og familiesenter, Alfheim | Alfheimvn 6 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Bufdir JSON-adresse: Postadresse : Postboks 2233, 3103 Tønsberg |
| `a736b9a7-0ea4-4e24-9b58-71ada437af8b` | Ole Tobias Olsens gate 19 | – | Har poststed men mangler gateadresse. Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `213fa944-e83c-4ee1-8f92-baf6ef05b65f` | KUS SKM | Storgata 31 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `e3a5849c-29f7-4261-ae71-d7fde1ae2bef` | Ringerike omsorgssenter for barn | Åsaveien 662 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Bufdir JSON-adresse: Postadresse : Postboks 2233, 3103 Tønsberg |
| `fb13e57b-22d6-427f-83bf-475975be1e7e` | Furene 8 | – | Har poststed men mangler gateadresse. Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `326092b3-850d-42a0-97a8-b7feebea3e8d` | FVK, FHT mf. Finnsnes | Hans Karolius vei 6 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `b5de7cff-100a-400f-8662-844658d28367` | KUS SKM, FVK, RK Harstad | Håkonsgt 4 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `d6e3728a-833a-45c6-9f8d-7f4f7c5e09f3` | Kvammen Gård | Hølondvegen 311 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `1c28a07e-abc6-4b00-87e0-af5fda4650f6` | Sogn og Fjordane ungdomssenter Meltunet - før brann | Sjukehusvegen  5 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `b19e31a3-d549-43e9-9ba3-095fdd479070` | Familievernkontoret i Molde | Storgata 12 - 14 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `ee9379ce-ceca-4641-9424-0e70945beaac` | Familievern Odda | Røldalsvegen 2 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `baa5bf7a-08f3-424f-9fd8-23038a1d5bda` | Familievern Stord | Torget 10 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `022fa3c0-9c3a-431c-a239-6dbf5d8f31c8` | Bodø behandlingsenter | Rønvikvn 9A,C | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `c65eb1d3-ccf7-49b4-aa98-119ab07eacd0` | Familievern Voss | Uttrågata 36 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `a4f8b4d6-4d7b-404c-83fd-1177427dc158` | Driftsavdeling region vest | Nedre Nøttveit 58 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `30bcb03f-45d2-4b07-aa1c-914917e2fcf6` | Bufetathus Haugesund | Haraldsgata 94 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Samme navn som 1 annen(e) eiendom: 9cd8ef03-11f7-4d9f-9543-ee3c5f2a2c8b |
| `fcd55797-687d-4ae4-8f7a-7ad07b0031f2` | Bufetathus Stavanger | Jåttåvågveien 10 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Samme navn som 1 annen(e) eiendom: e4a46d3c-d1a4-4816-8761-db333473e552 |
| `cdea14e5-f1f5-43b7-bd11-bf1703d328d4` | FVK Bodø | Storgata 27/29  | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `9cd8ef03-11f7-4d9f-9543-ee3c5f2a2c8b` | Bufetathus Haugesund | Rennesøygata 16 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Samme navn som 1 annen(e) eiendom: 30bcb03f-45d2-4b07-aa1c-914917e2fcf6 |
| `2f8605b9-b918-4979-8bb0-f9336dbf68d3` | Energivegen 13, 2260 Kirkenær | Energivegen 13 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `cda8c3bc-cbab-4c88-907e-ad61ced8b9d4` | Regionkontoret, Inntak, AT, FVK Alta | Løkkeveien 33 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `07a4c12b-6404-4603-b3f8-2ece9bcf6b79` | Oscarsgate 20, 0301 Oslo | Oscarsgate 20 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `00081f10-fa89-4d52-af07-f2b7dbe57cf7` | Henrik Gerners gate 14, 1530 Moss | Henrik Gerners gate 14 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `32645e00-1602-4f09-b1c6-14480a7ce410` | Familievern-kontoret i Kristiansund | Vågeveien 10 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `db1bf00d-bed7-4a47-81de-2f0e39435f32` | Tovdal | Austenå 370 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `23b34d63-66cb-4425-aba1-5ccb338bbda0` | ESF, FHT, RK Vadsø | Grensen 7 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `ca447380-524c-4ef9-bf0f-1f326241bfd9` | Regionkontoret region sør | Anton Jenssens gate 2 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `53181bf2-e205-4486-a30d-0342cc1e1ea6` | Bodø ungdomssentersenter | Skoleveien 9 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Bufdir JSON-adresse: Besøksadresse Rødstokken 16, 6856 Sogndal \n Postadresse Postboks 2233, 3103 Tønsberg |
| `9ca3a315-11e6-45a9-a3c3-589e6662de9b` | Lågen | Frogsvei 21-25 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `140a23a9-9c9e-4ff3-a879-8548981cf795` | Familievern-kontoret i Namsos | Abel Meyers gate 10 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `eab25d70-6d6f-498a-8217-c6537181e67e` | Grønlandsleiret 25, 0191 Oslo | Grønlandsleiret 25 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `0a84b12c-b439-4bb2-b3c3-f918640bd81b` | Nymosvingen 6, 2609 Lillehammer | Nymosvingen 6 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `ea0c6516-c284-422c-9b65-e030aa7d1a58` | Rena ungdoms- og familiesenter, Øst | Dr. Thorshaugsveg 8 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `2b901fbe-9ab1-4eae-890d-8521a9da338a` | Jong Ungdomshjem , hybel | Horniveien 100 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `3594d704-7e39-4fa7-9255-51c2654c7494` | Fosterhjemstjeneste avd. Ålesund, familievernkontoret Ålesun | Langelandsveien 17 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `74d40ee8-3370-4df0-8f79-01a4243481a9` | Ullsvei 16 | Kindsåsveien 2 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `247566b1-58b0-4a81-9fea-40523ecde657` | Øverbyvegen 88 -104 | Tokerudkollen 31-33 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Samme navn som 1 annen(e) eiendom: 33ee9f33-c71b-4f77-bd0e-cbce78cc3eef Bufdir JSON-adresse: Postadresse : Postbo |
| `13ffb54b-6d55-4305-86b3-ea82c9993117` | Toppen | Kirkegårdsveien 25 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Samme navn som 2 annen(e) eiendom: 08b57672-9f6a-4289-b3cb-6f47ac31f098, fecd2885-22b7-4a87-a7e3-793863604ce7 |
| `ce7970c1-f04d-4f09-9a62-2dad50ff4101` | Energivegen 17,2260 Kirkenær | Energivegen 17 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `1d6a85cc-827e-417c-9c4a-b0581c901824` | Jernbanevegen 70 | Jernbaneveien 70 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Bufdir JSON-adresse: Postadresse : Postboks 2233, 3103 Tønsberg Eiendomsnavn i DB ligner ikke Bufdir offisielt na |
| `5df186d2-0846-4a38-94a7-9bc87ef3a6dc` | Storgata 10- Gjøvik | Storgata 10 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `00f82124-85f5-4e69-b0e2-96335918eecd` | Bruvegen 6, 2260 Kirkenær | Bruvegen 6 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `5faead1e-e83e-4294-b78b-585edc1ba52b` | Veslekila 1 | Veslekila 3A | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Bufdir JSON-adresse: Postadresse : Postboks 2233, 3103 Tønsberg Eiendomsnavn i DB ligner ikke Bufdir offisielt na |
| `3dad633d-78cc-477e-8518-3dbdc4448883` | Trondheimsveien 205 | Trondheimsvegen - Jessheim 205 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Bufdir JSON-adresse: Postadresse : Postboks 2233, 3103 Tønsberg Eiendomsnavn i DB ligner ikke Bufdir offisielt na |
| `54bbf902-417b-4890-bc03-4dfebb575685` | Familievern Sogndal | Parkvegen 5 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `005ea20f-5be6-40ae-a2bf-28411c16c067` | Akershus ungdoms- og familiesenter, Sole | Njords vei 11 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Bufdir JSON-adresse: Postadresse : Postboks 2233, 3103 Tønsberg |
| `beba97af-e090-4f66-8689-10bba5094155` | Glynitveien 30, 1400 Ski | Glynitveien 30 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `0f9b6c1a-b779-4109-aefc-40f30f8a5566` | Storgata 11 | Storgaten 11 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `a127fa19-915f-4ecf-a38c-03f386b73192` | Strandsagvegen 2 D, 2383 Brumunddal | Strandsagvegen 2 D | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `db0495a5-fe18-42ce-afcf-2bdb1852c308` | Gågata 5, 2211 Kongsvinger | Gågata 5 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `c0e0b9e4-5ca8-45f8-af5d-b341baee7aff` | Tærudgata 16, 2004 Lillestrøm | Tærudgata 16 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `91a76803-c9a1-40ce-8df0-b5bea1fd936a` | Egge Gård, 3514 Hønefoss | Egge gård | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `a1f939b6-90b1-4138-82cd-ee0e507968a2` | FHT, ESF, MST, Inntak, RK, Bodø | Nordstrandveien 41 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `54fb49a0-43dd-40a5-ba7a-5cae4b64e271` | FHT, FVK, beredskapshjem, FIT Hammerfest | Sørøygt 10 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `d3a4f4d1-cdee-41e6-acc4-552ef5360382` | Snorres vei 2 | Snorres veg 2 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `59094e20-a3a1-402b-bd96-20ff1da242c3` | Sti omsorg AS | Storgata 56-58 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `a43ffccb-4d57-4082-b7f9-7433a3531a3c` | Elias Smiths vei 22-24, 1337 Sandvika | Elias Smiths vei 22-24 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `51791f47-6740-43c4-8575-a9dc319b0b4b` | Bufetats behandlingssenter Akershus/Østfold, Østlund | Stasjonsveien 16B | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Bufdir JSON-adresse: Postadresse : Postboks 2233, 3103 Tønsberg |
| `dc937552-4c5a-4cd5-91ea-5641bd32dc12` | FVK, Lofoten og Vesterålen | Nordnesveien 3 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Samme navn som 1 annen(e) eiendom: f9cdf6ff-74e6-45c7-b382-aecd5dea68cd |
| `99113427-c1e7-4c60-995d-acfe9b3072d3` | Lundebyveien 363, 1878 Hærland | Lundebyveien 363 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `00658fb2-21fd-48d2-a839-cc525e28afe2` | Østfold ungdoms- og familiesenter, Rokkeveien | Rokkeveien 502 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Bufdir JSON-adresse: Postadresse : Postboks 2233, 3103 Tønsberg |
| `53ade079-fcf4-49db-8b9a-a8205e0666da` | Bufetathus Drammen | Grønland 68 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `1ed4eef6-0577-4ad6-b7e3-3372fb2515eb` | Ullsvei 16, 1782 Halden | Ullsvei 16 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `3cd3d9a5-60f0-4d7c-8b41-b7fcbef30a94` | Sogn og Fjordane ungdomssenter Meltunet - midlertidig | Sophus Lie-vegen 5 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `6e0cdda3-3fcc-4113-a9a0-7d4ca7165dc9` | Uglevn 1, 1712 Grålum | Uglevn 1 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `93ccbcdb-5d45-4604-b702-6f748d669329` | Bufdir Tønsberg | Anton Jensens gt. 5 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `ade85975-f507-43fb-ad6c-1b0974619f65` | Fiskergata 22 | – | Har poststed men mangler gateadresse. Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `ccac64bf-b0a0-429a-94d8-10b14058e322` | Bufetathus Telemark | Schweigaardsgt 11 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `ec1c9fc5-fda8-49c6-87a9-5064c304af3b` | Lierfoss ungdoms- og familiesenter, Riserhagen | Riserveien 40A/B | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Bufdir JSON-adresse: Postadresse : Postboks 2233, 3103 Tønsberg |
| `d686c38e-22f6-481f-ba9a-0261088b64f8` | Familievern-kontoret i Levanger | Jernbanegata 11/13 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `de02cb91-c790-4edb-a291-d59b50db2016` | Storveien 1404/1408 | Storveien 1404 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Bufdir JSON-adresse: Postadresse : Postboks 2233, 3103 Tønsberg Eiendomsnavn i DB ligner ikke Bufdir offisielt na |
| `1eb61339-daa3-4148-8fdb-caa2f4e80b59` | Kanalveien 18, 2004 Lillestrøm | Kanalveien 18 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `a208ad6d-987a-4762-89c0-7199d9c36481` | Familievernkontoret Ringerike - Hallingdal, avdeling Ringeri | Bekkegata 2A | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `f338aff5-a4c8-4239-8c99-f3e9682abc0e` | FVK, kontorsted Narvik | Kongens gate 51-55 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `f77b5834-5e5f-4171-a6a4-7a587fbd7ca8` | FVK/NASAK, Karasjok | Fitnodatgeaidnu 41-43 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `4cf2a0d0-2513-4f27-a985-e22ac804d5e0` | Rådhusgata 16, 1380 Askim | Rådhusgata 16 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `63ac87b6-e0fb-499f-9471-00f4acebc8cc` | Bufdir Hovedkontor | Fredrik Selmers vei 3 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `6645f7f4-c796-4626-88f9-28a979c1ff1c` | Katfoss | Ilaugveien 1 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Samme navn som 1 annen(e) eiendom: da6ccfca-7a22-45ef-b260-3ed9cf7082b1 |
| `822d911a-efd2-472e-b67c-d8f0587290d7` | Stenliveien 7, 1784 Halden | Stenliveien 7 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `4e2851da-f658-4e5c-99b4-a48625028697` | Snytasvingen, 3519 Hønefoss | Askveien 132 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `be083c31-bc5e-479b-9f16-b5688b5f12ba` | Viktoria familiesenter | Østmarkveien 26 D/E | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `414bdc29-127d-4f77-8a93-e10f4c552e95` | Åsvangveien 2A | – | Har poststed men mangler gateadresse. Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Eiendomsnavn i DB ligner ikke Bufdir offisielt navn. |
| `ac1348ff-a869-4ab6-83d1-c955e561d178` | Thorøya Vaktmesterbolig | Thorøyaveien 1  | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Samme navn som 1 annen(e) eiendom: c9dc5d55-29ff-48f3-a295-5ef0d0bba9fd |
| `e103ebfa-80aa-44d1-8d4b-5d59e2d84f65` | Forbordsfjellvegen 119 | – | Har poststed men mangler gateadresse. Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `703281ea-2c49-4df3-8f7e-7fc892fad7f9` | Fosterhjemstjeneste Steinkjer, Inntak Steinkjer | Bomveien 3 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `d56dcc5b-6f7c-4736-943e-7d20d21d4852` | Ramsrudveien 32, 3518 Hønefoss | Ramsrudveien 32 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `7abe25ac-d08a-4754-8197-3b1e570251a4` | Bodø Familievernkontor | Storgata 27/29 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Eiendomsnavn i DB ligner ikke Bufdir offisielt navn. |
| `7bc51c8e-e44a-4113-ac98-86569bc972f6` | Bjørndalsvegen 178, 2150 Årnes | Bjørndalsvegen 178 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `820792dd-f380-4428-b2b9-b315f9702515` | ESF, FHT, RK, beredskapshjem, Tromsø | Storgata 70 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `005dcb0c-b7be-4c88-8f64-7cb38ce456bc` | Foreldre og barn Førde - Blåklokka | Svanehaugvegen 3 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `f51921e4-82f6-41e8-bc9c-1d332ef2650b` | Pirsenteret - Regionkontor | Havnegata 9 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Eiendomsnavn i DB ligner ikke Bufdir offisielt navn. |
| `e4a46d3c-d1a4-4816-8761-db333473e552` | Bufetathus Stavanger | Lagårdsveien 44 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Samme navn som 1 annen(e) eiendom: fcd55797-687d-4ae4-8f7a-7ad07b0031f2 |
| `9557fe2d-b215-49eb-9127-0c0326b69f1c` | Energiveien 14, 2069 Jessheim | Energiveien 14 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `9ce0b68b-69f0-432c-93c8-9d5c6757595e` | Gartneriveien 8, 2260 Kirkenær | Gartneriveien 8 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `69b4b796-e253-460b-9a78-7679576f7603` | Senter for foreldre og barn, Adm.lokaler | Frænaveien 16 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `60571f11-e626-49b5-9fc1-dd852c4a1fdc` | Orkdal barnevernsenter | Ljåmovein 10 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Bufdir JSON-adresse: \n \n Besøksadresse: Hølondvegen 311, 7223 Melhus \n Postadresse: Postboks 2233, 3103 Tønsbe |
| `b2ed1472-9ed7-4541-b44d-889766267a7a` | Glemmengaten 55, 1608 Fredrikstad | Glemmengaten 55 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `c9dc5d55-29ff-48f3-a295-5ef0d0bba9fd` | Thorøya Vaktmesterbolig | Thorøyaveien 1 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Samme navn som 1 annen(e) eiendom: ac1348ff-a869-4ab6-83d1-c955e561d178 |
| `ca70f9bf-e3ad-41ec-b101-1f14acc31ace` | Marmorveien 23, 2818 Gjøvik | Marmorveien 23 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `ce4f7830-b8b4-43a8-ab00-ae428e2bcc61` | F3 ungdom - Sjukehusvegen 5 - tillegg (kontor) | Sjukehusvegen 5 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `f9cdf6ff-74e6-45c7-b382-aecd5dea68cd` | FVK, Lofoten og Vesterålen | Markedsgt 20 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Samme navn som 1 annen(e) eiendom: dc937552-4c5a-4cd5-91ea-5641bd32dc12 |
| `f4b42df1-b101-43c7-8201-5cc2fc178897` | Torget 6, 2000 Lillestrøm | Torget 6 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `fedc9785-2496-4281-881c-d7101dc2b902` | Østfold ungdoms- og familiesenter, Tune | Vestrevei 1 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Bufdir JSON-adresse: Postadresse : Postboks 2233, 3103 Tønsberg |
| `3cdeca26-c322-40a8-87cd-513b371d4ad9` | Bufetathus Førde | Storehagen 1b | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `4643807b-915b-4b35-bb4a-1ca1eb8ee2f9` | Senter for familie og barn, Molde | Bastian Withs gt 11 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `0bc51285-f295-4130-8cde-7ec5f6afa16f` | FHT, kontorsted Sandnessjøen | Torolv Kveldulvsonsgt 39 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `f1634112-dbcd-4a56-94c5-e45c8115ff8d` | KUS SKM, psykologspesialist Kirkenes | Wiulls gate 3 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `7546345a-1548-4737-be79-9a3632083f35` | Erik Børresen | Wildhagensvei 17 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `632db590-145b-4b33-ac90-3e7b2d0585ed` | Storveien 121, 1621 Gressvik | Storveien 121 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |

## missing_geolocation

| property_id | Navn (kort) | Adresse | Merknad |
|---|---|---|---|
| `d31e5212-bb29-4b34-a562-50ae1cc00cac` | Svenner | – | Mangler gateadresse og poststed (postnr/by/kommune). |
| `db80e8ba-d8c4-403a-a348-ce71e20405ab` | Nyhuset | – | Mangler gateadresse og poststed (postnr/by/kommune). |
| `7b3c92f6-da1a-4e01-b0f4-700626626c67` | Harebakken | – | Mangler gateadresse og poststed (postnr/by/kommune). |
| `3703fa90-8923-4722-8d6a-9f7dc367ed28` | Husafjellheimen ungdomsheim | – | Mangler gateadresse og poststed (postnr/by/kommune). |
| `8128d2e0-1c43-411a-a3f2-1b00c78b2a41` | Trøndelag behandlingssenter for ungdom | – | Mangler gateadresse og poststed (postnr/by/kommune). |
| `43f1364d-2459-43bf-9436-a021ba39ba67` | Skjerven rusbehandling ungdom | – | Mangler gateadresse og poststed (postnr/by/kommune). |
| `a0368488-7c15-4b34-81ca-188220fb2049` | Indre finnmark FV | – | Mangler gateadresse og poststed (postnr/by/kommune). |
| `46c6e40c-7a86-4a1d-b1c2-2b8214a39f56` | Familievernkontoret Nedre Romerike | – | Mangler gateadresse og poststed (postnr/by/kommune). |
| `b22828d5-67c3-4fe4-88a9-a80e4476a6cf` | Familievernkontoret Øvre Romerike Glåmdal | – | Mangler gateadresse og poststed (postnr/by/kommune). |
| `e02a2a09-c288-4bd1-8d3b-d550cab1ecef` | MST Sunnmøre | – | Mangler gateadresse og poststed (postnr/by/kommune). |
| `b2bd061a-e273-4086-90bb-0daacfc3fbdd` | Familievernkontoret Sunnmøre | – | Mangler gateadresse og poststed (postnr/by/kommune). |
| `f026ebf4-a770-4504-a692-7c3e3b8e5b17` | Familievernkontoret Romsdal | – | Mangler gateadresse og poststed (postnr/by/kommune). |
| `fd5433fe-8385-4e74-94a9-547d27924208` | Husafjellheimen, familiehjem | – | Mangler gateadresse og poststed (postnr/by/kommune). |
| `b72a7453-cf35-40a4-9787-440099f1b216` | SFU avd.Meltunet | – | Mangler gateadresse og poststed (postnr/by/kommune). |
| `60d63432-048a-4f24-b474-6834dc65600b` | Familievernkontoret i Vestfold | – | Mangler gateadresse og poststed (postnr/by/kommune). |
| `ebbdd7ba-8fe0-47bf-b5dd-558a7b45809e` | Avdeling familiebehandling | – | Mangler gateadresse og poststed (postnr/by/kommune). |
| `c2c995ae-704d-4d4b-a42c-6b7c40f4d57b` | Vestfold barne- og familiesenter Adm | – | Mangler gateadresse og poststed (postnr/by/kommune). |
| `a73acead-4093-4c9e-bdb1-218475e61ca4` | Sogndal ungdomsenter-adm. | – | Mangler gateadresse og poststed (postnr/by/kommune). |
| `a119a2b5-5f4e-4a74-88b1-5e27c4c9a7bf` | Alta og Hammerfest familievernkontor | – | Mangler gateadresse og poststed (postnr/by/kommune). |
| `ea771518-032a-4dcf-941c-36af2cb05177` | SKM opplæring fosterhjem | – | Mangler gateadresse og poststed (postnr/by/kommune). |
| `02d465c4-0ab0-4fe1-904d-835d880350db` | Avdeling for ung.no | – | Mangler gateadresse og poststed (postnr/by/kommune). |
| `532154d0-bc0c-448c-a427-f8658c9292ea` | Skjoldvegen Søfteland | – | Mangler gateadresse og poststed (postnr/by/kommune). |
| `75f22971-47ac-42db-8c62-e1cb04ac65ea` | MST Agder 1 | – | Mangler gateadresse og poststed (postnr/by/kommune). |
| `13b14373-dd15-4396-bc78-1665d841896d` | Familievernkontoret Nordmøre | – | Mangler gateadresse og poststed (postnr/by/kommune). |
| `4219418e-e5b4-46ef-9e41-c8cb747e958a` | Familievernkontoret Namdalen | – | Mangler gateadresse og poststed (postnr/by/kommune). |
| `a6a76e19-e0d8-4884-ae73-7ef2e97b06bc` | Familievernkontoret Asker og Bærum | – | Mangler gateadresse og poststed (postnr/by/kommune). |
| `9c2c5529-e35f-460c-a197-351b1c1925a7` | Familievernkontoret Enerhaugen | – | Mangler gateadresse og poststed (postnr/by/kommune). |
| `87076fca-8f00-4c20-be14-9870168f7de2` | Familievernkontoret Homansbyen | – | Mangler gateadresse og poststed (postnr/by/kommune). |
| `a0ba18fc-915a-4c0f-8a1b-ea11065fa7fb` | Familievernkontoret Østfold | – | Mangler gateadresse og poststed (postnr/by/kommune). |
| `e281ef91-5df0-4290-83f2-71aa72295f3a` | Grøterød ungdomshjem | – | Mangler gateadresse og poststed (postnr/by/kommune). |
| `21b13a36-cc1f-44e9-88fb-c3d541ab0a08` | Agder ungdomshjem | – | Mangler gateadresse og poststed (postnr/by/kommune). |
| `9d0bcf0e-0697-4284-b5b4-5d21ce59c199` | Agder ungdomssenter | – | Mangler gateadresse og poststed (postnr/by/kommune). |
| `df788c1f-d80b-475f-a391-91ec6aef96fa` | Vestfold ungdomssenter | – | Mangler gateadresse og poststed (postnr/by/kommune). |

## missing_street_address_only

| property_id | Navn (kort) | Adresse | Merknad |
|---|---|---|---|
| `1f0b433f-9348-4891-a83c-759c5e3b1987` | Solerødveien 50 | – | Har poststed men mangler gateadresse. |
| `0bcb1ac0-e33c-4e71-8c55-0d01443195d8` | Rogalandsgata 35A | – | Har poststed men mangler gateadresse. |
| `a736b9a7-0ea4-4e24-9b58-71ada437af8b` | Ole Tobias Olsens gate 19 | – | Har poststed men mangler gateadresse. Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `fb13e57b-22d6-427f-83bf-475975be1e7e` | Furene 8 | – | Har poststed men mangler gateadresse. Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `ade85975-f507-43fb-ad6c-1b0974619f65` | Fiskergata 22 | – | Har poststed men mangler gateadresse. Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `2c1227fd-959e-429d-9eea-e463c78b9e79` | Haralosen 2 | – | Har poststed men mangler gateadresse. |
| `414bdc29-127d-4f77-8a93-e10f4c552e95` | Åsvangveien 2A | – | Har poststed men mangler gateadresse. Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Eiendomsnavn i DB ligner ikke Bufdir offisielt navn. |
| `e103ebfa-80aa-44d1-8d4b-5d59e2d84f65` | Forbordsfjellvegen 119 | – | Har poststed men mangler gateadresse. Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `8d4f529e-2e58-4cb1-aefe-4a17cb5218f5` | Femmælen | – | Har poststed men mangler gateadresse. |
| `9eeb0536-eed6-4255-8e14-ca3fcade3a98` | Haralosen 24 | – | Har poststed men mangler gateadresse. |
| `b186b5a0-372a-4331-80d7-605861055456` | Hotvetveien 57 | – | Har poststed men mangler gateadresse. |

## name_looks_like_address

| property_id | Navn (kort) | Adresse | Merknad |
|---|---|---|---|
| `2f8605b9-b918-4979-8bb0-f9336dbf68d3` | Energivegen 13, 2260 Kirkenær | Energivegen 13 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `07a4c12b-6404-4603-b3f8-2ece9bcf6b79` | Oscarsgate 20, 0301 Oslo | Oscarsgate 20 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `00081f10-fa89-4d52-af07-f2b7dbe57cf7` | Henrik Gerners gate 14, 1530 Moss | Henrik Gerners gate 14 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `eab25d70-6d6f-498a-8217-c6537181e67e` | Grønlandsleiret 25, 0191 Oslo | Grønlandsleiret 25 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `0a84b12c-b439-4bb2-b3c3-f918640bd81b` | Nymosvingen 6, 2609 Lillehammer | Nymosvingen 6 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `da964e7f-4307-4413-ba69-bee455d3859f` | Kirkenærtunet 27, 2260 Kirkenær | Kirkenærtunet 27 |  |
| `ce7970c1-f04d-4f09-9a62-2dad50ff4101` | Energivegen 17,2260 Kirkenær | Energivegen 17 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `00f82124-85f5-4e69-b0e2-96335918eecd` | Bruvegen 6, 2260 Kirkenær | Bruvegen 6 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `beba97af-e090-4f66-8689-10bba5094155` | Glynitveien 30, 1400 Ski | Glynitveien 30 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `a127fa19-915f-4ecf-a38c-03f386b73192` | Strandsagvegen 2 D, 2383 Brumunddal | Strandsagvegen 2 D | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `db0495a5-fe18-42ce-afcf-2bdb1852c308` | Gågata 5, 2211 Kongsvinger | Gågata 5 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `c0e0b9e4-5ca8-45f8-af5d-b341baee7aff` | Tærudgata 16, 2004 Lillestrøm | Tærudgata 16 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `91a76803-c9a1-40ce-8df0-b5bea1fd936a` | Egge Gård, 3514 Hønefoss | Egge gård | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `a43ffccb-4d57-4082-b7f9-7433a3531a3c` | Elias Smiths vei 22-24, 1337 Sandvika | Elias Smiths vei 22-24 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `99113427-c1e7-4c60-995d-acfe9b3072d3` | Lundebyveien 363, 1878 Hærland | Lundebyveien 363 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `1ed4eef6-0577-4ad6-b7e3-3372fb2515eb` | Ullsvei 16, 1782 Halden | Ullsvei 16 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `6e0cdda3-3fcc-4113-a9a0-7d4ca7165dc9` | Uglevn 1, 1712 Grålum | Uglevn 1 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `1eb61339-daa3-4148-8fdb-caa2f4e80b59` | Kanalveien 18, 2004 Lillestrøm | Kanalveien 18 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `4cf2a0d0-2513-4f27-a985-e22ac804d5e0` | Rådhusgata 16, 1380 Askim | Rådhusgata 16 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `822d911a-efd2-472e-b67c-d8f0587290d7` | Stenliveien 7, 1784 Halden | Stenliveien 7 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `4e2851da-f658-4e5c-99b4-a48625028697` | Snytasvingen, 3519 Hønefoss | Askveien 132 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `d56dcc5b-6f7c-4736-943e-7d20d21d4852` | Ramsrudveien 32, 3518 Hønefoss | Ramsrudveien 32 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `7bc51c8e-e44a-4113-ac98-86569bc972f6` | Bjørndalsvegen 178, 2150 Årnes | Bjørndalsvegen 178 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `9557fe2d-b215-49eb-9127-0c0326b69f1c` | Energiveien 14, 2069 Jessheim | Energiveien 14 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `9ce0b68b-69f0-432c-93c8-9d5c6757595e` | Gartneriveien 8, 2260 Kirkenær | Gartneriveien 8 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `b2ed1472-9ed7-4541-b44d-889766267a7a` | Glemmengaten 55, 1608 Fredrikstad | Glemmengaten 55 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `ca70f9bf-e3ad-41ec-b101-1f14acc31ace` | Marmorveien 23, 2818 Gjøvik | Marmorveien 23 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `f4b42df1-b101-43c7-8201-5cc2fc178897` | Torget 6, 2000 Lillestrøm | Torget 6 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |
| `632db590-145b-4b33-ac90-3e7b2d0585ed` | Storveien 121, 1621 Gressvik | Storveien 121 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). |

## property_name_differs_from_bufdir_official

| property_id | Navn (kort) | Adresse | Merknad |
|---|---|---|---|
| `33ee9f33-c71b-4f77-bd0e-cbce78cc3eef` | Øverbyvegen 88 -104 | Øverbyveien 104 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Samme navn som 1 annen(e) eiendom: 247566b1-58b0-4a81-9fea-40523ecde657 Eiendomsnavn i DB ligner ikke Bufdir offi |
| `438c4047-1861-47f4-b655-1b8f283f86cc` | Feilregistert | Nedre Nattland 69 | Bufdir JSON-adresse: Besøksadresse Nedre Nattland 69, 5099 Bergen \n Postadresse Postboks 2233, 3103 Tønsberg Eiendomsnavn i DB ligner ikke Bufdir offisielt navn. |
| `b8fcd912-7c52-4294-907c-8ada717c9268` | Skjoldvegen Skjold | Skjoldvegen 51 | Lagret institution_name avviker fra JSON (cache utdatert?). JSON: Fana og Ytrebygda ungdomssenter, Skjold Bufdir JSON-adresse: Besøksadresse Skjoldvegen 51/55, 5221 Nesttun \n Postadresse Postboks 223 |
| `fd0d6ac2-c7ce-4ad6-baed-b74c4cea8482` | Sundstedtråkka | Storgaten 62-64 | Samme navn som 1 annen(e) eiendom: 338600a3-649d-4b0d-9b76-124aaf50771f Bufdir JSON-adresse: Besøksadresse \n Haugsundgata 62, 3303 Hokksund \n Postadresse \n Postboks 2230, 3103 Tønsberg \n Be Eiendo |
| `247566b1-58b0-4a81-9fea-40523ecde657` | Øverbyvegen 88 -104 | Tokerudkollen 31-33 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Samme navn som 1 annen(e) eiendom: 33ee9f33-c71b-4f77-bd0e-cbce78cc3eef Bufdir JSON-adresse: Postadresse : Postbo |
| `1d6a85cc-827e-417c-9c4a-b0581c901824` | Jernbanevegen 70 | Jernbaneveien 70 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Bufdir JSON-adresse: Postadresse : Postboks 2233, 3103 Tønsberg Eiendomsnavn i DB ligner ikke Bufdir offisielt na |
| `5faead1e-e83e-4294-b78b-585edc1ba52b` | Veslekila 1 | Veslekila 3A | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Bufdir JSON-adresse: Postadresse : Postboks 2233, 3103 Tønsberg Eiendomsnavn i DB ligner ikke Bufdir offisielt na |
| `555393a1-3efb-4b8a-b179-bbfca9fa61ee` | Nes | Nesverkveien 190 | Bufdir JSON-adresse: Adresse \n Frogs vei 19, 3611 Kongsberg \n Postadresse \n Postboks 2233, 3103 Tønsberg Eiendomsnavn i DB ligner ikke Bufdir offisielt navn. |
| `3dad633d-78cc-477e-8518-3dbdc4448883` | Trondheimsveien 205 | Trondheimsvegen - Jessheim 205 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Bufdir JSON-adresse: Postadresse : Postboks 2233, 3103 Tønsberg Eiendomsnavn i DB ligner ikke Bufdir offisielt na |
| `1679f1b0-cdb7-4a06-a067-4a34e15dc2f4` | Lerketoppen | Grimestadveien 69 | Bufdir JSON-adresse: Besøksadresse: Grimestadveien 69, 3160 Stokke \n Postadresse: Postboks 2233, 3103 Tønsberg Eiendomsnavn i DB ligner ikke Bufdir offisielt navn. |
| `de02cb91-c790-4edb-a291-d59b50db2016` | Storveien 1404/1408 | Storveien 1404 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Bufdir JSON-adresse: Postadresse : Postboks 2233, 3103 Tønsberg Eiendomsnavn i DB ligner ikke Bufdir offisielt na |
| `414bdc29-127d-4f77-8a93-e10f4c552e95` | Åsvangveien 2A | – | Har poststed men mangler gateadresse. Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Eiendomsnavn i DB ligner ikke Bufdir offisielt navn. |
| `f0831c60-192d-4f41-9863-520dbe471caa` | Kantum | Baneveien  19 | Samme navn som 1 annen(e) eiendom: adda3311-6723-4274-8d59-89be53598d59 Eiendomsnavn i DB ligner ikke Bufdir offisielt navn. |
| `7abe25ac-d08a-4754-8197-3b1e570251a4` | Bodø Familievernkontor | Storgata 27/29 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Eiendomsnavn i DB ligner ikke Bufdir offisielt navn. |
| `f51921e4-82f6-41e8-bc9c-1d332ef2650b` | Pirsenteret - Regionkontor | Havnegata 9 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Eiendomsnavn i DB ligner ikke Bufdir offisielt navn. |
| `60571f11-e626-49b5-9fc1-dd852c4a1fdc` | Orkdal barnevernsenter | Ljåmovein 10 | Mangler kobling til regnskap (unit_id_erp, department_code og koststed_kode er tomme). Bufdir JSON-adresse: \n \n Besøksadresse: Hølondvegen 311, 7223 Melhus \n Postadresse: Postboks 2233, 3103 Tønsbe |
