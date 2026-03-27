"""Chromium Sysroot Packages

Debian packages providing system shared libraries required by Chromium
headless-shell on Linux. Used by playwright_chromium_with_sysroot.
"""

# AUTO-GENERATED: DO NOT MODIFY
#
# Update using the following command:
#
# ```
# bazel run //tools/update_versions:update_chromium_sysroot
# ```

CHROMIUM_SYSROOT_PACKAGES = {
    "linux-aarch64": [
        {
            "integrity": "sha256-eToJYcrRVAvcYhfxS1ROsbJ+2pUmdfTX0VD1R/DBltc=",
            "name": "libasound2t64",
            "urls": ["http://ports.ubuntu.com/ubuntu-ports/pool/main/a/alsa-lib/libasound2t64_1.2.11-1build2_arm64.deb"],
        },
        {
            "integrity": "sha256-eizlMsqoV8TX2LztCoFD0cfPijCT+NqSbgJSUu9wEX8=",
            "name": "libatk-bridge2.0-0t64",
            "urls": ["http://ports.ubuntu.com/ubuntu-ports/pool/main/a/at-spi2-core/libatk-bridge2.0-0t64_2.52.0-1build1_arm64.deb"],
        },
        {
            "integrity": "sha256-iTljOzkSxkdvP1AcLoqg/MaB29NDsKgTi/DtWvjpp3o=",
            "name": "libatk1.0-0t64",
            "urls": ["http://ports.ubuntu.com/ubuntu-ports/pool/main/a/at-spi2-core/libatk1.0-0t64_2.52.0-1build1_arm64.deb"],
        },
        {
            "integrity": "sha256-xl8TdQemZclp+dFYyPYxiLMIA35mtIvKheoufPMbuE4=",
            "name": "libatspi2.0-0t64",
            "urls": ["http://ports.ubuntu.com/ubuntu-ports/pool/main/a/at-spi2-core/libatspi2.0-0t64_2.52.0-1build1_arm64.deb"],
        },
        {
            "integrity": "sha256-14IN6uRVEKPKHB9uMrqi6LEqI0pBDRheQudendX81to=",
            "name": "libcairo2",
            "urls": ["http://ports.ubuntu.com/ubuntu-ports/pool/main/c/cairo/libcairo2_1.18.0-3build1_arm64.deb"],
        },
        {
            "integrity": "sha256-e3JhMV9tOE0fNC3UaG1218dIqD9Ilc7/nIoozLYi6V4=",
            "name": "libcups2t64",
            "urls": ["http://ports.ubuntu.com/ubuntu-ports/pool/main/c/cups/libcups2t64_2.4.7-1.2ubuntu7_arm64.deb"],
        },
        {
            "integrity": "sha256-wmm+KKLtRdCPhcoufrijM/fvWwGgUvStVh5oNP5MiWQ=",
            "name": "libdbus-1-3",
            "urls": ["http://ports.ubuntu.com/ubuntu-ports/pool/main/d/dbus/libdbus-1-3_1.14.10-4ubuntu4_arm64.deb"],
        },
        {
            "integrity": "sha256-ynM3PTWpXHyRLWOP4UxUMFTpN+9juEWWZcO3DIPuPyI=",
            "name": "libdrm2",
            "urls": ["http://ports.ubuntu.com/ubuntu-ports/pool/main/libd/libdrm/libdrm2_2.4.120-2build1_arm64.deb"],
        },
        {
            "integrity": "sha256-hYnzF+faz/a5WLmiOV/aPJ1iMEs9oTkKU629s6+zNDY=",
            "name": "libgbm1",
            "urls": ["http://ports.ubuntu.com/ubuntu-ports/pool/main/m/mesa/libgbm1_24.0.5-1ubuntu1_arm64.deb"],
        },
        {
            "integrity": "sha256-dSuhQg8RRSosPJyLimiYje/E6jnS0moDcmdnIqJ+vgw=",
            "name": "libglib2.0-0t64",
            "urls": ["http://ports.ubuntu.com/ubuntu-ports/pool/main/g/glib2.0/libglib2.0-0t64_2.80.0-6ubuntu1_arm64.deb"],
        },
        {
            "integrity": "sha256-C9WZQSbEGqBao4CVSjyyrlagqOvjaKDgGkEf3MDLnGg=",
            "name": "libnspr4",
            "urls": ["http://ports.ubuntu.com/ubuntu-ports/pool/main/n/nspr/libnspr4_4.35-1.1build1_arm64.deb"],
        },
        {
            "integrity": "sha256-jPOHhsiAi+wYc3WPccjGNDh2d/FhBLpMXOJIV0bErJY=",
            "name": "libnss3",
            "urls": ["http://ports.ubuntu.com/ubuntu-ports/pool/main/n/nss/libnss3_3.98-1build1_arm64.deb"],
        },
        {
            "integrity": "sha256-SWS8TGHfQl5BoyEI5YpJPPMRqDZqnLJSLoygfjCoHrQ=",
            "name": "libpango-1.0-0",
            "urls": ["http://ports.ubuntu.com/ubuntu-ports/pool/main/p/pango1.0/libpango-1.0-0_1.52.1+ds-1build1_arm64.deb"],
        },
        {
            "integrity": "sha256-FtEK5dJ/Gg/rBUAB/yshO1Gs0piU+G/wiMMe6+umX+M=",
            "name": "libx11-6",
            "urls": ["http://ports.ubuntu.com/ubuntu-ports/pool/main/libx/libx11/libx11-6_1.8.7-1build1_arm64.deb"],
        },
        {
            "integrity": "sha256-VIPl0Zu/oo6WHZUWRZROd2PpQyYqwX4hayhw2DWX8xk=",
            "name": "libxcb1",
            "urls": ["http://ports.ubuntu.com/ubuntu-ports/pool/main/libx/libxcb/libxcb1_1.15-1ubuntu2_arm64.deb"],
        },
        {
            "integrity": "sha256-lPDW1gLQDprFPTB1CYl2cvETLIdeJXagb9nz3NAN2B4=",
            "name": "libxcomposite1",
            "urls": ["http://ports.ubuntu.com/ubuntu-ports/pool/main/libx/libxcomposite/libxcomposite1_0.4.5-1build3_arm64.deb"],
        },
        {
            "integrity": "sha256-b1SGX9E0kua9kEXhjEgnDNbEIsRHxVMaFzWKJnSOXVA=",
            "name": "libxdamage1",
            "urls": ["http://ports.ubuntu.com/ubuntu-ports/pool/main/libx/libxdamage/libxdamage1_1.1.6-1build1_arm64.deb"],
        },
        {
            "integrity": "sha256-EUCrrNjSPLg8xj+5rrsVogHi3dv1ynn9mZwMvRgdAIg=",
            "name": "libxext6",
            "urls": ["http://ports.ubuntu.com/ubuntu-ports/pool/main/libx/libxext/libxext6_1.3.4-1build2_arm64.deb"],
        },
        {
            "integrity": "sha256-iE/GVgxai8kftrfQZ/VX2AiMzuhq0ZdLalcIWsEh6N4=",
            "name": "libxfixes3",
            "urls": ["http://ports.ubuntu.com/ubuntu-ports/pool/main/libx/libxfixes/libxfixes3_6.0.0-2build1_arm64.deb"],
        },
        {
            "integrity": "sha256-TvaLnVaXGjEZ9AaE9SogC+XHwb+MXvQwotUC6RC/i2E=",
            "name": "libxkbcommon0",
            "urls": ["http://ports.ubuntu.com/ubuntu-ports/pool/main/libx/libxkbcommon/libxkbcommon0_1.6.0-1build1_arm64.deb"],
        },
        {
            "integrity": "sha256-dHBjJ2Tx/emH52CFDCvliXPiZfQbK7gBXEFdJHiY0sQ=",
            "name": "libxrandr2",
            "urls": ["http://ports.ubuntu.com/ubuntu-ports/pool/main/libx/libxrandr/libxrandr2_1.5.2-2build1_arm64.deb"],
        },
        {
            "integrity": "sha256-TfKu+nOVFASZAzszmpYWSSXx/TA531Jmm4estr7CDxk=",
            "name": "libfontconfig1",
            "urls": ["http://ports.ubuntu.com/ubuntu-ports/pool/main/f/fontconfig/libfontconfig1_2.15.0-1.1ubuntu2_arm64.deb"],
        },
        {
            "integrity": "sha256-f2HY+w4XuUNERUIRupEMbWN1KmPWKPLoY0TlRYOUja4=",
            "name": "libfreetype6",
            "urls": ["http://ports.ubuntu.com/ubuntu-ports/pool/main/f/freetype/libfreetype6_2.13.2+dfsg-1build3_arm64.deb"],
        },
        {
            "integrity": "sha256-9s6gy+YXUZSAqzUBFm6rcJKpp1MyyxhsMO7oEH2jgbk=",
            "name": "libexpat1",
            "urls": ["http://ports.ubuntu.com/ubuntu-ports/pool/main/e/expat/libexpat1_2.6.1-2build1_arm64.deb"],
        },
        {
            "integrity": "sha256-CjrtqxXZsNenSwsENnbwyqzBBPGIvhagCBltvCDp4uI=",
            "name": "libxrender1",
            "urls": ["http://ports.ubuntu.com/ubuntu-ports/pool/main/libx/libxrender/libxrender1_0.9.10-1.1build1_arm64.deb"],
        },
        {
            "integrity": "sha256-cCEpMV4Z8bvwSgPYxox0CxR7TQSrZ3IH5LclxeoXRHg=",
            "name": "libpangocairo-1.0-0",
            "urls": ["http://ports.ubuntu.com/ubuntu-ports/pool/main/p/pango1.0/libpangocairo-1.0-0_1.52.1+ds-1build1_arm64.deb"],
        },
        {
            "integrity": "sha256-gQZcGA4wMClQob05Qo0zV5cSbvidwpIviSFmeHINTso=",
            "name": "libpixman-1-0",
            "urls": ["http://ports.ubuntu.com/ubuntu-ports/pool/main/p/pixman/libpixman-1-0_0.42.2-1build1_arm64.deb"],
        },
        {
            "integrity": "sha256-NI0HMv+Vcfldb/GDc6k+gnv+AEdNeS716QcebdYYYFw=",
            "name": "libxau6",
            "urls": ["http://ports.ubuntu.com/ubuntu-ports/pool/main/libx/libxau/libxau6_1.0.9-1build6_arm64.deb"],
        },
        {
            "integrity": "sha256-a5bbuuTlFayPMtbaz8tq/RJmEYQAqFrnyz+IeJUBf1M=",
            "name": "libxdmcp6",
            "urls": ["http://ports.ubuntu.com/ubuntu-ports/pool/main/libx/libxdmcp/libxdmcp6_1.1.3-0ubuntu6_arm64.deb"],
        },
        {
            "integrity": "sha256-K23sDUAHBoX0zjRtILBk/F4RijFJ8wvohGUlGYW0lu0=",
            "name": "libwayland-server0",
            "urls": ["http://ports.ubuntu.com/ubuntu-ports/pool/main/w/wayland/libwayland-server0_1.22.0-2.1build1_arm64.deb"],
        },
        {
            "integrity": "sha256-8dJY5x/UKCDLx93QyuOuC5KOJ7RuC2OHfKpq/75lN1I=",
            "name": "libwayland-client0",
            "urls": ["http://ports.ubuntu.com/ubuntu-ports/pool/main/w/wayland/libwayland-client0_1.22.0-2.1build1_arm64.deb"],
        },
    ],
    "linux-x86_64": [
        {
            "integrity": "sha256-wvDKowhph2eRujSb70kH1c/sR7jP0a6YiaBdzg/rfDk=",
            "name": "libasound2t64",
            "urls": ["http://archive.ubuntu.com/ubuntu/pool/main/a/alsa-lib/libasound2t64_1.2.11-1build2_amd64.deb"],
        },
        {
            "integrity": "sha256-IrfUfjwPeVOnjTz9MJ0bIHcQhd6SIPvmEMCYm56AjJs=",
            "name": "libatk-bridge2.0-0t64",
            "urls": ["http://archive.ubuntu.com/ubuntu/pool/main/a/at-spi2-core/libatk-bridge2.0-0t64_2.52.0-1build1_amd64.deb"],
        },
        {
            "integrity": "sha256-QsXUsAlU8XwsPEuGaET2keuLbVe/CLWSA+ZfEtyEpPk=",
            "name": "libatk1.0-0t64",
            "urls": ["http://archive.ubuntu.com/ubuntu/pool/main/a/at-spi2-core/libatk1.0-0t64_2.52.0-1build1_amd64.deb"],
        },
        {
            "integrity": "sha256-1oas5AgOypwtbOjeaTkqWsVshGcBiUwIWJItTONBodc=",
            "name": "libatspi2.0-0t64",
            "urls": ["http://archive.ubuntu.com/ubuntu/pool/main/a/at-spi2-core/libatspi2.0-0t64_2.52.0-1build1_amd64.deb"],
        },
        {
            "integrity": "sha256-lpULMGiJ/25CSLuTewo7VuctrPZD/nMiFM43Xw9ruzY=",
            "name": "libcairo2",
            "urls": ["http://archive.ubuntu.com/ubuntu/pool/main/c/cairo/libcairo2_1.18.0-3build1_amd64.deb"],
        },
        {
            "integrity": "sha256-iiiYcGjtzTp2rHDenvJRkpTiuKmpi5obrElcQlwOojM=",
            "name": "libcups2t64",
            "urls": ["http://archive.ubuntu.com/ubuntu/pool/main/c/cups/libcups2t64_2.4.7-1.2ubuntu7_amd64.deb"],
        },
        {
            "integrity": "sha256-u7VRERgqRND+l6hBIEB+F7tuI9QeJnDXOqePYZ4p76I=",
            "name": "libdbus-1-3",
            "urls": ["http://archive.ubuntu.com/ubuntu/pool/main/d/dbus/libdbus-1-3_1.14.10-4ubuntu4_amd64.deb"],
        },
        {
            "integrity": "sha256-9ftOfOF5IcxGb7eRGr+RSV/7GBs2dy9o4ugstiFwMRI=",
            "name": "libdrm2",
            "urls": ["http://archive.ubuntu.com/ubuntu/pool/main/libd/libdrm/libdrm2_2.4.120-2build1_amd64.deb"],
        },
        {
            "integrity": "sha256-v/rSHSODQp1tvsg5W6jYR2oO1p5+Cxw+8vJ9qZIRsgA=",
            "name": "libgbm1",
            "urls": ["http://archive.ubuntu.com/ubuntu/pool/main/m/mesa/libgbm1_24.0.5-1ubuntu1_amd64.deb"],
        },
        {
            "integrity": "sha256-YpNZ6RX0Rmz5yw+mw4Jw2a8eA+KPq1V84xl31as08T0=",
            "name": "libglib2.0-0t64",
            "urls": ["http://archive.ubuntu.com/ubuntu/pool/main/g/glib2.0/libglib2.0-0t64_2.80.0-6ubuntu1_amd64.deb"],
        },
        {
            "integrity": "sha256-5XnnLQkfbHoT9adWwxBlsVquW4GEDWGwaTVaoig8B7Q=",
            "name": "libnspr4",
            "urls": ["http://archive.ubuntu.com/ubuntu/pool/main/n/nspr/libnspr4_4.35-1.1build1_amd64.deb"],
        },
        {
            "integrity": "sha256-iCR/4Ntc1MJzt90CbZ3tT/m6gotiQ30SovHCq8KUaNI=",
            "name": "libnss3",
            "urls": ["http://archive.ubuntu.com/ubuntu/pool/main/n/nss/libnss3_3.98-1build1_amd64.deb"],
        },
        {
            "integrity": "sha256-Cd+lyIGrJz7GvBgwrc79xAf81hkxbmj7Jso6I9D8n1Q=",
            "name": "libpango-1.0-0",
            "urls": ["http://archive.ubuntu.com/ubuntu/pool/main/p/pango1.0/libpango-1.0-0_1.52.1+ds-1build1_amd64.deb"],
        },
        {
            "integrity": "sha256-OX+ENHR2o8V4aznz/28PgoZus9i+bSrT7+rfAZ7+W4A=",
            "name": "libx11-6",
            "urls": ["http://archive.ubuntu.com/ubuntu/pool/main/libx/libx11/libx11-6_1.8.7-1build1_amd64.deb"],
        },
        {
            "integrity": "sha256-4cZhHRGtc5gybxvwKK/DTDsUxR2RejQmuWbtS5aH+lg=",
            "name": "libxcb1",
            "urls": ["http://archive.ubuntu.com/ubuntu/pool/main/libx/libxcb/libxcb1_1.15-1ubuntu2_amd64.deb"],
        },
        {
            "integrity": "sha256-oS1dmucLeYy78oQIDq4yuHNnVh/JwkSS9kG4hgrA8wg=",
            "name": "libxcomposite1",
            "urls": ["http://archive.ubuntu.com/ubuntu/pool/main/libx/libxcomposite/libxcomposite1_0.4.5-1build3_amd64.deb"],
        },
        {
            "integrity": "sha256-aJH68yXpluvSjvU+u5wEPclvZzJ1AEkK/8PonTZtNe0=",
            "name": "libxdamage1",
            "urls": ["http://archive.ubuntu.com/ubuntu/pool/main/libx/libxdamage/libxdamage1_1.1.6-1build1_amd64.deb"],
        },
        {
            "integrity": "sha256-RXg5aans6de3tzO4xgmBWExTxrxe47QtKV0vgNEoVnk=",
            "name": "libxext6",
            "urls": ["http://archive.ubuntu.com/ubuntu/pool/main/libx/libxext/libxext6_1.3.4-1build2_amd64.deb"],
        },
        {
            "integrity": "sha256-DuEBXMzQYySeAcDNC/RfUTyKyaHl5IUHDBLmkZJFXko=",
            "name": "libxfixes3",
            "urls": ["http://archive.ubuntu.com/ubuntu/pool/main/libx/libxfixes/libxfixes3_6.0.0-2build1_amd64.deb"],
        },
        {
            "integrity": "sha256-K5yutCPvtUApahyyC4csxjDCOQhAfstcHHh6YXYi1mQ=",
            "name": "libxkbcommon0",
            "urls": ["http://archive.ubuntu.com/ubuntu/pool/main/libx/libxkbcommon/libxkbcommon0_1.6.0-1build1_amd64.deb"],
        },
        {
            "integrity": "sha256-8pVaXllPVyS1itJB2SMeoZHLNldKDV5cprZhzUHWJW0=",
            "name": "libxrandr2",
            "urls": ["http://archive.ubuntu.com/ubuntu/pool/main/libx/libxrandr/libxrandr2_1.5.2-2build1_amd64.deb"],
        },
        {
            "integrity": "sha256-orwFz+8CH9uEKFA2+Y7aXr7DxLejePWqK9ulxNPY1YY=",
            "name": "libfontconfig1",
            "urls": ["http://archive.ubuntu.com/ubuntu/pool/main/f/fontconfig/libfontconfig1_2.15.0-1.1ubuntu2_amd64.deb"],
        },
        {
            "integrity": "sha256-Mh3ak09i+orwhSmoxMNLDsBA8XLAqUXc4QuL5vEBSRc=",
            "name": "libfreetype6",
            "urls": ["http://archive.ubuntu.com/ubuntu/pool/main/f/freetype/libfreetype6_2.13.2+dfsg-1build3_amd64.deb"],
        },
        {
            "integrity": "sha256-cwspSXISKJzaijE55pOjU4rwy1eEbCT4B9G7KTpZHF4=",
            "name": "libexpat1",
            "urls": ["http://archive.ubuntu.com/ubuntu/pool/main/e/expat/libexpat1_2.6.1-2build1_amd64.deb"],
        },
        {
            "integrity": "sha256-1wvYMa6+jUg0td0u2Y3ybda9J/EELEdUO9f2bfGuIuo=",
            "name": "libxrender1",
            "urls": ["http://archive.ubuntu.com/ubuntu/pool/main/libx/libxrender/libxrender1_0.9.10-1.1build1_amd64.deb"],
        },
        {
            "integrity": "sha256-mM9fyQdsKRH+IN/B5BzY9oaiu11TmxEF+rGBBbDbE3Y=",
            "name": "libpangocairo-1.0-0",
            "urls": ["http://archive.ubuntu.com/ubuntu/pool/main/p/pango1.0/libpangocairo-1.0-0_1.52.1+ds-1build1_amd64.deb"],
        },
        {
            "integrity": "sha256-2cKTHExCRhXuq53Vrgi/xgi4ToA8HTzN3zGScNshNCE=",
            "name": "libpixman-1-0",
            "urls": ["http://archive.ubuntu.com/ubuntu/pool/main/p/pixman/libpixman-1-0_0.42.2-1build1_amd64.deb"],
        },
        {
            "integrity": "sha256-5A0p8dGmI5O6yu3r4No9kAYIQVKp9+XgKSk/CM4cXIA=",
            "name": "libxau6",
            "urls": ["http://archive.ubuntu.com/ubuntu/pool/main/libx/libxau/libxau6_1.0.9-1build6_amd64.deb"],
        },
        {
            "integrity": "sha256-vNM2/OEc4qRfNND5XmmAryJSnyIUfo+YwVblzujuQrs=",
            "name": "libxdmcp6",
            "urls": ["http://archive.ubuntu.com/ubuntu/pool/main/libx/libxdmcp/libxdmcp6_1.1.3-0ubuntu6_amd64.deb"],
        },
        {
            "integrity": "sha256-7b+ktoV2ka6SLMdop1P6sjDu6elWqizk8uqo2a13fco=",
            "name": "libwayland-server0",
            "urls": ["http://archive.ubuntu.com/ubuntu/pool/main/w/wayland/libwayland-server0_1.22.0-2.1build1_amd64.deb"],
        },
        {
            "integrity": "sha256-avCu1B11FJvqIvpGjwHrBY/+PjXvB/8vE/uIqQOHiB0=",
            "name": "libwayland-client0",
            "urls": ["http://archive.ubuntu.com/ubuntu/pool/main/w/wayland/libwayland-client0_1.22.0-2.1build1_amd64.deb"],
        },
    ],
}
