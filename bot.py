import argparse
from datetime import date, datetime, timedelta

import maskpass
import pause
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

TIMEOUT = 5  # Timeout time in seconds
LOGIN_BUTTON_XPATH = "/html/body/div/div[3]/div/a"


def get_element_by_xpath(driver, xpath, timeout=TIMEOUT):
    return WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((By.XPATH, xpath))
    )


def book_gn(
    driver: webdriver.Firefox,
    booking_days_offset: float = 14,
    booking_hours_offset: float = 14,
    booking_minutes_offset: float = 9,
    booking_seconds_offset: float = 0,
    guests: "list[str]" = ["Guest"],
):
    email = input("email: ")
    password = maskpass.askpass(prompt="password: ")

    # Get login page
    driver.get("https://www2.trinity.ox.ac.uk/secure/meals/default.aspx")

    # Input email
    get_element_by_xpath(driver, "//*[@id='i0116']").send_keys(email)
    get_element_by_xpath(driver, "//*[@id='idSIButton9']").click()

    # Input password
    get_element_by_xpath(driver, "//*[@id='i0118']").send_keys(password)
    get_element_by_xpath(driver, "//*[@id='idSIButton9']").click()

    # Check if login was successful
    try:
        get_element_by_xpath(driver, "//*[@id='idDiv_SAOTCS_Title']")
    except Exception:
        print("Invalid email/password, aborting...")
        raise Exception

    # OTP
    otp = maskpass.askpass(prompt="otp: ")
    for _ in range(100):
        try:
            get_element_by_xpath(
                driver,
                (
                    "/html/body/div/form[1]/div/div/div[2]/div[1]/div/div/div/div/div"
                    "/div[2]/div[2]/div/div[2]/div/div[2]/div/div[1]/div"
                ),
            ).click()
            get_element_by_xpath(driver, "//*[@id='idTxtBx_SAOTCC_OTC']").send_keys(otp)
            get_element_by_xpath(driver, "//*[@id='idSubmit_SAOTCC_Continue']").click()
        except Exception:
            break

    # Wait until time to book
    print("Waiting for the right time to book...")
    today_midnight = datetime.combine(date.today(), datetime.min.time())
    delta = timedelta(
        hours=booking_hours_offset,
        minutes=booking_minutes_offset,
        seconds=booking_seconds_offset,
    )
    booking_time = today_midnight + delta
    pause.until(booking_time)

    # Refresh page
    driver.get("https://www2.trinity.ox.ac.uk/secure/meals/default.aspx")

    # Book spots
    print("Booking...")
    booking_day = date.today() + timedelta(days=booking_days_offset)
    date_html_title = booking_day.strftime("%d %B")
    get_element_by_xpath(driver, f"//*[@title='{date_html_title}']").click()
    get_element_by_xpath(driver, "//*[@id='ContentPlaceHolder1_btnBook']").click()
    get_element_by_xpath(driver, "//*[@id='ContentPlaceHolder1_btnBook']").click()

    successfully_booked_guests = []
    for guest in guests:
        try:
            get_element_by_xpath(
                driver, "//*[@id='ContentPlaceHolder1_btnBook']"
            ).click()
            get_element_by_xpath(
                driver, "//*[@id='ContentPlaceHolder1_txtGuestName']"
            ).send_keys(guest)
            get_element_by_xpath(
                driver, "//*[@id='ContentPlaceHolder1_btnBook']"
            ).click()
            successfully_booked_guests.append(guest)
        except Exception:
            print(f"Failed to book guest {guest}")

    print(
        f"Booked for {booking_day}, with guest(s): {', '.join(successfully_booked_guests)}."
    )

    driver.close()


if __name__ == "__main__":
    # Handle arguments
    parser = argparse.ArgumentParser(description="A bot to help you book guest nights.")
    parser.add_argument(
        "--guests",
        nargs="+",
        type=str,
        default=["Guesto"],
        help="Names of the guests you want to book for.",
    )
    parser.add_argument(
        "--head",
        action="store_true",
        help="Run the bot in 'non-headless mode' (with a viewable browser instance).",
    )
    parser.add_argument(
        "--bd",
        type=int,
        default=14,
        help="The number of days to offset the booking relative to today. Defaults to 14 days.",
    )
    parser.add_argument(
        "--offset",
        nargs=3,
        type=int,
        default=[24, 0, 0],
        help="The 'hours minutes seconds' offset of the booking. Defaults to '24 0 0'.",
    )

    args = parser.parse_args()

    firefox_options = Options()
    if not args.head:
        firefox_options.add_argument("--headless")
    driver = webdriver.Firefox(options=firefox_options)

    try:
        book_gn(
            driver,
            booking_days_offset=args.bd,
            booking_hours_offset=args.offset[0],
            booking_minutes_offset=args.offset[1],
            booking_seconds_offset=args.offset[2],
            guests=args.guests,
        )
    except Exception:
        print("Bot failed, aborting...")
        driver.close()
