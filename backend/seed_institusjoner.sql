-- BEFS: Seed institusjoner fra CSV
-- Datafelt: Region, Målgruppe, Enhetsnr., Enhetens/Institusjonens navn, 
--           Avdelingens koststed, Navn på avdeling, Antall kvalitetssikrede, Antall budsjetterte

-- 1. Fjern NOT NULL constraints for felt som ikke er i CSV
ALTER TABLE properties ALTER COLUMN address DROP NOT NULL;
ALTER TABLE properties ALTER COLUMN postal_code DROP NOT NULL;
ALTER TABLE properties ALTER COLUMN city DROP NOT NULL;

-- 2. Opprett admin-bruker
INSERT INTO users (id, email, hashed_password, full_name, role, is_active, is_verified, region, created_at, updated_at)
VALUES (
  gen_random_uuid(),
  'admin@befs.no',
  '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VTtYBKjKPe8Kmy',
  'Admin Bruker',
  'ADMIN',
  true,
  true,
  'Øst',
  NOW(),
  NOW()
);

-- 3. Institusjoner (properties) - kun datafelt fra CSV
-- Mapping: Region→region, Målgruppe→affiliation, Enhetsnr.→lokalisering_id, 
--          Institusjonsnavn→name, approved_places, budgeted_places

INSERT INTO properties (property_id, lokalisering_id, name, region, affiliation, approved_places, budgeted_places, created_at, updated_at) VALUES
-- Øst
(gen_random_uuid(), '262', 'Hedmark ungdoms- og familiesenter', 'Øst', '1 Akutt', 16, 14, NOW(), NOW()),
(gen_random_uuid(), '261', 'Akershus ungdoms- og familiesenter', 'Øst', '1 Akutt', 12, 11, NOW(), NOW()),
(gen_random_uuid(), '227', 'Østfold ungdoms- og familiesenter', 'Øst', '1 Akutt', 31, 23, NOW(), NOW()),
(gen_random_uuid(), '226', 'Lierfoss ungdoms- og familiesenter', 'Øst', '1 Akutt', 14, 14, NOW(), NOW()),
(gen_random_uuid(), '271', 'Bufetats behandlingssenter Akershus/Østfold', 'Øst', '1 Akutt', 16, 16, NOW(), NOW()),
(gen_random_uuid(), '228', 'Kirkenær barnevern- og omsorgssenter', 'Øst', '3 Omsorg ungdom', 16, 11, NOW(), NOW()),
(gen_random_uuid(), '254', 'Innlandet barnevernsenter', 'Øst', '3 Omsorg ungdom', 21, 21, NOW(), NOW()),
(gen_random_uuid(), '272', 'Jong ungdomshjem', 'Øst', '4 Rus', 10, 8, NOW(), NOW()),
-- Sør
(gen_random_uuid(), '308', 'Sundstedåkka ungdomssenter akutt', 'Sør', '1 Akutt', 8, 8, NOW(), NOW()),
(gen_random_uuid(), '309', 'Klokkerhuset ungdomssenter akutt', 'Sør', '1 Akutt', 6, 6, NOW(), NOW()),
(gen_random_uuid(), '336', 'St.Hansgården ungdomssenter akutt', 'Sør', '1 Akutt', 6, 6, NOW(), NOW()),
(gen_random_uuid(), '337', 'Barkåker ungdssenter akutt', 'Sør', '1 Akutt', 8, 8, NOW(), NOW()),
(gen_random_uuid(), '338', 'Grøterød ungdomshjem', 'Sør', '1 Akutt', 10, 9, NOW(), NOW()),
(gen_random_uuid(), '342', 'Stokke barnesenter', 'Sør', '2 Omsorg barn', 4, 4, NOW(), NOW()),
(gen_random_uuid(), '317', 'Telemark ungdomssenter', 'Sør', '3 Omsorg ungdom', 12, 9, NOW(), NOW()),
(gen_random_uuid(), '318', 'Agder ungdomshjem', 'Sør', '3 Omsorg ungdom', 11, 9, NOW(), NOW()),
(gen_random_uuid(), '339', 'Lågen ungdomshjem', 'Sør', '3 Omsorg ungdom', 10, 9, NOW(), NOW()),
(gen_random_uuid(), '340', 'Thorøya Ungdomshjem', 'Sør', '3 Omsorg ungdom', 6, 6, NOW(), NOW()),
(gen_random_uuid(), '335', 'Lunde behandlingssenter', 'Sør', '3 Behandlingssentre', 6, 6, NOW(), NOW()),
(gen_random_uuid(), '331', 'Agder ungdomssenter', 'Sør', '4 Behandling høy risiko, eks MultifunC', 11, 8, NOW(), NOW()),
(gen_random_uuid(), '343', 'Katfoss behandling ungdom', 'Sør', '4 Behandling høy risiko, eks MultifunC', 3, 3, NOW(), NOW()),
(gen_random_uuid(), '341', 'Skjerven', 'Sør', '4 Rus', 4, 4, NOW(), NOW()),
-- Vest
(gen_random_uuid(), '406', 'Bergen Akuttsenter Ungdom', 'Vest', '1 Akutt', 11, 11, NOW(), NOW()),
(gen_random_uuid(), '407', 'Stavanger Akuttsenter Ungdom', 'Vest', '1 Akutt', 10, 8, NOW(), NOW()),
(gen_random_uuid(), '421', 'Skjoldvegen barnevernsenter', 'Vest', '3 Omsorg ungdom', 7, 7, NOW(), NOW()),
(gen_random_uuid(), '422', 'Stavanger ungdomssenter', 'Vest', '3 Omsorg ungdom', 8, 8, NOW(), NOW()),
(gen_random_uuid(), '428', 'Kasa Ungdomssenter', 'Vest', '3 Omsorg ungdom', 18, 17, NOW(), NOW()),
(gen_random_uuid(), '429', 'Sogndal Ungdomssenter', 'Vest', '3 Omsorg ungdom', 4, 4, NOW(), NOW()),
(gen_random_uuid(), '431', 'Sandnes Ungdomssenter', 'Vest', '2 Omsorg barn', 8, 8, NOW(), NOW()),
(gen_random_uuid(), '452', 'Fana og Ytrebygda ungdomssenter', 'Vest', '4 Behandling høy risiko, eks MultifunC', 3, 3, NOW(), NOW()),
(gen_random_uuid(), '424', 'Sogn og Fjordane ungdomssenter', 'Vest', '3 Omsorg ungdom', 4, 4, NOW(), NOW()),
(gen_random_uuid(), '451', 'Sogn og Fjordane ungdomssenter behandling', 'Vest', '4 Behandling høy risiko, eks MultifunC', 4, 3, NOW(), NOW()),
(gen_random_uuid(), '427', 'Bjørgvin Ungdomssenter', 'Vest', '4 Rus', 8, 8, NOW(), NOW()),
-- Midt-Norge
(gen_random_uuid(), '512', 'Vikhovlia akuttsenter', 'Midt-Norge', '1 Akutt', 6, 6, NOW(), NOW()),
(gen_random_uuid(), '520', 'Kvammen akuttinstitusjon', 'Midt-Norge', '1 Akutt', 10, 8, NOW(), NOW()),
(gen_random_uuid(), '534', 'Humla Akuttsenter', 'Midt-Norge', '1 Akutt', 4, 4, NOW(), NOW()),
(gen_random_uuid(), '544', 'Sunnmørsheimen akuttinstitusjon', 'Midt-Norge', '1 Akutt', 2, 2, NOW(), NOW()),
(gen_random_uuid(), '505', 'Spillumheimen ungdomsheim', 'Midt-Norge', '3 Omsorg ungdom', 0, 0, NOW(), NOW()),
(gen_random_uuid(), '510', 'Karienborg ungdomsheim', 'Midt-Norge', '3 Omsorg ungdom', 6, 6, NOW(), NOW()),
(gen_random_uuid(), '513', 'Ranheim Vestre', 'Midt-Norge', '3 Omsorg ungdom', 7, 6, NOW(), NOW()),
(gen_random_uuid(), '521', 'Gilantunet ungdomshjem', 'Midt-Norge', '3 Omsorg ungdom', 7, 7, NOW(), NOW()),
(gen_random_uuid(), '525', 'Clausenengen ungdomshjem', 'Midt-Norge', '3 Omsorg ungdom', 4, 4, NOW(), NOW()),
(gen_random_uuid(), '529', 'Kollen ungdomsbase', 'Midt-Norge', '3 Omsorg ungdom', 8, 7, NOW(), NOW()),
(gen_random_uuid(), '532', 'Husafjellheimen ungdomsheim', 'Midt-Norge', '3 Omsorg ungdom', 6, 6, NOW(), NOW()),
(gen_random_uuid(), '533', 'Sunnmørsheimen ungdomsheim', 'Midt-Norge', '4 Behandling lav risiko', 4, 4, NOW(), NOW()),
(gen_random_uuid(), '511', 'Trøndelag behandlingssenter for ungdom', 'Midt-Norge', '4 MultifunC', 10, 9, NOW(), NOW()),
-- Nord
(gen_random_uuid(), '619', 'Alta Ungdomssenter', 'Nord', '1 Akutt', 7, 4, NOW(), NOW()),
(gen_random_uuid(), '624', 'Røvika Ungdomssenter', 'Nord', '1 Akutt', 5, 4, NOW(), NOW()),
(gen_random_uuid(), '655', 'Tromsø ungdomssenter', 'Nord', '1 Akutt', 5, 5, NOW(), NOW()),
(gen_random_uuid(), '658', 'Sollia Barne- og ungdomssenter', 'Nord', '3 Omsorg ungdom', 5, 4, NOW(), NOW()),
(gen_random_uuid(), '656', 'Bodø behandlingssenter', 'Nord', '3 Behandlingssentre', 5, 5, NOW(), NOW()),
(gen_random_uuid(), '648', 'Nye Kvæfjord ungdomssenter', 'Nord', '3 Omsorg ungdom', 13, 13, NOW(), NOW()),
(gen_random_uuid(), '650', 'Nye Lamo ungdomssenter', 'Nord', '3 Omsorg ungdom', 5, 5, NOW(), NOW()),
(gen_random_uuid(), '663', 'Silsand Ungdomssenter', 'Nord', '4 Behandling høy risiko, eks MultifunC', 3, 3, NOW(), NOW()),
(gen_random_uuid(), '631', 'Yttrabekken Ungdomshjem', 'Nord', '4 Behandling høy risiko, eks MultifunC', 3, 3, NOW(), NOW());

-- 4. Verifiser
SELECT 'Brukere:' as tabell, count(*) as antall FROM users
UNION ALL
SELECT 'Institusjoner:', count(*) FROM properties;

SELECT region, count(*) as antall, sum(approved_places) as godkjente_plasser, sum(budgeted_places) as budsjetterte_plasser 
FROM properties 
GROUP BY region 
ORDER BY region;
