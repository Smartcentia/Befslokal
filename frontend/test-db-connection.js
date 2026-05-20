const { PrismaClient } = require('@prisma/client');
const prisma = new PrismaClient();

async function testConnection() {
  try {
    console.log('🔗 Testing connection to restored database...\n');

    const result = await prisma.$queryRaw`
      SELECT
        current_database() as db,
        current_user as user,
        (SELECT COUNT(*) FROM properties) as property_count
    `;

    console.log('✅ Connection successful!');
    console.log('📊 Database:', result[0].db);
    console.log('👤 User:', result[0].user);
    console.log('🏢 Properties found:', result[0].property_count);
    console.log('\n🎉 Database restored successfully!\n');

  } catch (error) {
    console.error('❌ Connection failed:', error.message);
    process.exit(1);
  } finally {
    await prisma.$disconnect();
  }
}

testConnection();
