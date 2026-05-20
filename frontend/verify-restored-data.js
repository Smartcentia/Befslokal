const { PrismaClient } = require('@prisma/client');
const prisma = new PrismaClient();

async function verify() {
  try {
    console.log('🔎 Verifying restored data...');

    const info = await prisma.$queryRaw`
      SELECT current_database() as db, current_user as user, version();
    `;

    const counts = await prisma.$queryRaw`
      SELECT
        (SELECT COUNT(*) FROM properties) AS properties,
        (SELECT COUNT(*) FROM contracts) AS contracts,
        (SELECT COUNT(*) FROM parties) AS parties,
        (SELECT COUNT(*) FROM units) AS units;
    `;

    const samples = await prisma.$queryRaw`
      SELECT property_id, name, address, city, usage
      FROM properties
      WHERE name IS NOT NULL
      ORDER BY name
      LIMIT 10;
    `;

    console.log('✅ Connection');
    console.log('  DB:', info[0].db);
    console.log('  User:', info[0].user);
    console.log('  Version:', info[0].version);

    console.log('\n📊 Counts');
    console.log('  Properties:', counts[0].properties);
    console.log('  Contracts:', counts[0].contracts);
    console.log('  Parties:', counts[0].parties);
    console.log('  Units:', counts[0].units);

    console.log('\n🏠 Sample properties');
    for (const row of samples) {
      console.log(`  - ${row.property_id}: ${row.name} (${row.city})`);
    }

    console.log('\n✔️ Verification complete');
  } catch (err) {
    console.error('❌ Verification failed:', err.message);
    process.exit(1);
  } finally {
    await prisma.$disconnect();
  }
}

verify();
