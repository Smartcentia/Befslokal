-- SQL script to create 5 admin users
-- Users are created with ADMIN role and email_verified=true (no email confirmation needed)

-- Insert admin users (using ON CONFLICT to handle existing users)
INSERT INTO users (user_id, email, name, role, email_verified, mfa_enabled, region, created_at)
VALUES 
  (gen_random_uuid(), 'oystein.moller.frich@bufdir.no', 'Øystein Møller Frich', 'admin', true, true, NULL, NOW()),
  (gen_random_uuid(), 'ove.braten@bufdir.no', 'Ove Bråten', 'admin', true, true, NULL, NOW()),
  (gen_random_uuid(), 'larstony.laberget@bufdir.no', 'Larstony Laberget', 'admin', true, true, NULL, NOW()),
  (gen_random_uuid(), 'frankvevle@gmail.com', 'Frank Vevle', 'admin', true, true, NULL, NOW()),
  (gen_random_uuid(), 'frankvevle@hotmail.com', 'Frank Vevle', 'admin', true, true, NULL, NOW())
ON CONFLICT (email) DO UPDATE 
SET 
  role = 'admin',
  email_verified = true,
  mfa_enabled = true;

-- Verify the users were created/updated
SELECT 
  email, 
  name, 
  role, 
  email_verified,
  mfa_enabled,
  region
FROM users 
WHERE email IN (
  'oystein.moller.frich@bufdir.no',
  'ove.braten@bufdir.no',
  'larstony.laberget@bufdir.no',
  'frankvevle@gmail.com',
  'frankvevle@hotmail.com'
)
ORDER BY email;
