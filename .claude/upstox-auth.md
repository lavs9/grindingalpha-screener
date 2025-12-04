Upstox Authentication requires login using API key etc and credentials which gives access token which is valid till 23:59 PM for that day. Every next day in morning at 8 we have to get new access token for that day. 

Sample code for login is below. 

Important points for dev
1. Access_token should be part of a database table so that it can be looked up quickly and TTL etc can also be maintained
2. API Key and secret is shared as part of ENV file 
3. for now i can set redirect URL to localhost
4. Other personal details have to be part of env, I have added them. 

@app.post("/auth/automate-login", tags=["Authentication"])
async def automate_upstox_login(req: UpstoxLoginRequest):
    """
    Automate Upstox login using Playwright and TOTP.
    Returns tokens if successful.
    """
    mobile = req.mobile
    pin = req.pin
    totp_secret = req.totp_secret

    async def run_automation():
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36"
            )
            page = await context.new_page()

            endpoint = (
                "https://api.upstox.com/v2/login/authorization/dialog"
                f"?response_type=code"
                f"&client_id={settings.UPSTOX_API_KEY}"
                f"&redirect_uri={settings.UPSTOX_REDIRECT_URI}"
            )
            await page.goto(endpoint, wait_until="domcontentloaded", timeout=30000)

            # Enter mobile number
            await page.wait_for_selector("#mobileNum", timeout=30000)
            await page.fill("#mobileNum", mobile)
            await page.click("#getOtp")

            # Generate TOTP
            otp = pyotp.TOTP(totp_secret).now()
            await page.wait_for_selector("#otpNum", timeout=30000)
            await page.fill("#otpNum", otp)
            await page.click("#continueBtn")

            # Enter PIN
            await page.wait_for_selector("#pinCode", timeout=30000)
            await page.fill("#pinCode", pin)
            await page.click("#pinContinueBtn")
            await page.wait_for_timeout(2000)

            # Wait for redirect and extract code
            await page.wait_for_url(f"{settings.UPSTOX_REDIRECT_URI}*", timeout=30000)
            url = page.url
            print(url)
            await browser.close()
            return url

    try:
        url = await run_automation()
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(url)
        code = parse_qs(parsed.query).get("code", [None])[0]
        if not code:
            return JSONResponse({"success": False, "error": "No code found in redirect URL"}, status_code=400)
        # Exchange code for tokens (reuse callback logic)
        token_url = "https://api.upstox.com/v2/login/authorization/token"
        payload = {
            "code": code,
            "client_id": settings.UPSTOX_API_KEY,
            "client_secret": settings.UPSTOX_API_SECRET,
            "redirect_uri": settings.UPSTOX_REDIRECT_URI,
            "grant_type": "authorization_code"
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }
        encoded_payload = urllib.parse.urlencode(payload)
        #print("Token exchange payload:", encoded_payload)
        #print("Headers:", headers)
        resp = requests.post(token_url, data=encoded_payload, headers=headers)
        #print("Upstox token endpoint response:")
        #print("Status code:", resp.status_code)
        #print("Response text:", resp.text)
        try:
            resp.raise_for_status()
            tokens = resp.json()
            token_manager.store_token(
                access_token=tokens.get("access_token"),
                refresh_token=tokens.get("refresh_token")
            )
            return {"success": True, "tokens": tokens}
        except Exception as e:
            return JSONResponse({
                "success": False,
                "error": str(e),
                "status_code": resp.status_code if 'resp' in locals() else None,
                "response_text": resp.text if 'resp' in locals() else None
            }, status_code=500)
    except Exception as e:
        error_response = {
            "success": False,
            "error": str(e),
            "status_code": None,
            "response_text": None
        }
        return JSONResponse(error_response, status_code=500)


References

https://upstox.com/developer/api-documentation/login