import asyncio
import aiosmtplib

async def test_smtp2go(port, use_tls=False, start_tls=False):
    print(f"\nTesting SMTP2GO on port {port} (use_tls={use_tls}, start_tls={start_tls})...")
    smtp = aiosmtplib.SMTP(
        hostname='mail.smtp2go.com',
        port=port,
        use_tls=use_tls,
        start_tls=start_tls,
        timeout=20
    )
    try:
        await smtp.connect()
        print(f"  Connected to port {port}")
        await smtp.ehlo()
        print(f"  EHLO successful")
        await smtp.login('qumail_smtp', 'y5UIscS3vTimj8jM')
        print(f"  ✅ SMTP2GO LOGIN SUCCESS on port {port}!")
        await smtp.quit()
        return True
    except Exception as e:
        print(f"  ❌ Port {port} failed: {type(e).__name__}: {e}")
        return False

async def main():
    # Try multiple ports SMTP2GO supports
    ports = [
        (2525, False, True),   # STARTTLS
        (8025, False, True),   # STARTTLS alt
        (587, False, True),    # STARTTLS standard
        (465, True, False),    # SSL/TLS
    ]
    for port, use_tls, start_tls in ports:
        success = await test_smtp2go(port, use_tls, start_tls)
        if success:
            print(f"\n🎉 Working port found: {port}")
            break

if __name__ == "__main__":
    asyncio.run(main())
