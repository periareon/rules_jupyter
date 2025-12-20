"""Pandoc Versions

A mapping of platform to integrity of the archive for said platform for each version of Pandoc available.
"""

# AUTO-GENERATED: DO NOT MODIFY
#
# Update using the following command:
#
# ```
# bazel run //tools/update_versions:update_pandoc
# ```

PANDOC_VERSIONS = {
    "3.0": {
        "linux-aarch64": {
            "integrity": "sha256-bAk1VL11o8RDGqlhPTEWKy0XRfT0aK9utr/+/0CrDdA=",
            "strip_prefix": "pandoc-3.0",
            "url": "https://github.com/jgm/pandoc/releases/download/3.0/pandoc-3.0-linux-arm64.tar.gz",
        },
        "linux-x86_64": {
            "integrity": "sha256-D+Lvg2amG5KW70qFErmi1KzQVsf5LOfgzIKt2WDCzI8=",
            "strip_prefix": "pandoc-3.0",
            "url": "https://github.com/jgm/pandoc/releases/download/3.0/pandoc-3.0-linux-amd64.tar.gz",
        },
        "windows-x86_64": {
            "integrity": "sha256-/c7F3ew192+l/irnQvws5x1pT9sXxXfwz04/Yjqdias=",
            "strip_prefix": "pandoc-3.0",
            "url": "https://github.com/jgm/pandoc/releases/download/3.0/pandoc-3.0-windows-x86_64.zip",
        },
    },
    "3.0.1": {
        "linux-aarch64": {
            "integrity": "sha256-TjRB7YMfY+tiS6QICh+9qkaXOQ1klJc9DE8uW6EJ5XM=",
            "strip_prefix": "pandoc-3.0.1",
            "url": "https://github.com/jgm/pandoc/releases/download/3.0.1/pandoc-3.0.1-linux-arm64.tar.gz",
        },
        "linux-x86_64": {
            "integrity": "sha256-uLAFGjwnq1gCuyoJHI3VzbZYjOc1am1cTmT78CIl2gQ=",
            "strip_prefix": "pandoc-3.0.1",
            "url": "https://github.com/jgm/pandoc/releases/download/3.0.1/pandoc-3.0.1-linux-amd64.tar.gz",
        },
        "windows-x86_64": {
            "integrity": "sha256-MsjeC9IF6vQR0ZkKHs9tmm9n+INr053oDqX2ImAo2fw=",
            "strip_prefix": "pandoc-3.0.1",
            "url": "https://github.com/jgm/pandoc/releases/download/3.0.1/pandoc-3.0.1-windows-x86_64.zip",
        },
    },
    "3.1": {
        "linux-aarch64": {
            "integrity": "sha256-UB1m3ojG6dFD5mMd7RUs7XQhvDK28WytqxiyBkkW/mM=",
            "strip_prefix": "pandoc-3.1",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1/pandoc-3.1-linux-arm64.tar.gz",
        },
        "linux-x86_64": {
            "integrity": "sha256-N95r6QBV2afhtOM4TNf8TELhOKd/Yt3uwS82K/o+4Y4=",
            "strip_prefix": "pandoc-3.1",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1/pandoc-3.1-linux-amd64.tar.gz",
        },
        "windows-x86_64": {
            "integrity": "sha256-Ie+SlMkfuea9EGEm0+5nE5UQ6g9WJWu40Ddtl8mrPSM=",
            "strip_prefix": "pandoc-3.1",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1/pandoc-3.1-windows-x86_64.zip",
        },
    },
    "3.1.1": {
        "linux-aarch64": {
            "integrity": "sha256-1dYrrTWpi1psdC5BOhSLXijmK36zW6Dgi8gotc8cu1Q=",
            "strip_prefix": "pandoc-3.1.1",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.1/pandoc-3.1.1-linux-arm64.tar.gz",
        },
        "linux-x86_64": {
            "integrity": "sha256-UrJfARVRfjIEegbYIeY3KRCAJ70G2WBf6OrA+oPgv4E=",
            "strip_prefix": "pandoc-3.1.1",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.1/pandoc-3.1.1-linux-amd64.tar.gz",
        },
        "windows-x86_64": {
            "integrity": "sha256-qznn0HgPD0vmUOgnOL+qr7vVce4pXkxEC8+Z77WgcXQ=",
            "strip_prefix": "pandoc-3.1.1",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.1/pandoc-3.1.1-windows-x86_64.zip",
        },
    },
    "3.1.10": {
        "linux-aarch64": {
            "integrity": "sha256-ZazHvoH9blBWuK15OqHHNvT3w0yy02XiphFgUlRXaMM=",
            "strip_prefix": "pandoc-3.1.10",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.10/pandoc-3.1.10-linux-arm64.tar.gz",
        },
        "linux-x86_64": {
            "integrity": "sha256-lbpYlwnmxkNEyUmejLlt+XMPTxBaL9mr5izkRW8W9+k=",
            "strip_prefix": "pandoc-3.1.10",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.10/pandoc-3.1.10-linux-amd64.tar.gz",
        },
        "macos-aarch64": {
            "integrity": "sha256-YaLtvDShnnNszZP5VYHKfnHErhz+/GRjJNJNwM2WtL4=",
            "strip_prefix": "pandoc-3.1.10-arm64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.10/pandoc-3.1.10-arm64-macOS.zip",
        },
        "macos-x86_64": {
            "integrity": "sha256-bK4G3S7GnOYhHcBfU7M1byUXnlbxzbAe++fC69LxzAE=",
            "strip_prefix": "pandoc-3.1.10-x86_64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.10/pandoc-3.1.10-x86_64-macOS.zip",
        },
        "windows-x86_64": {
            "integrity": "sha256-KMDvfY6EghpOQXXBbuICWnXemL95qeCFy4qHvmLmhcU=",
            "strip_prefix": "pandoc-3.1.10",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.10/pandoc-3.1.10-windows-x86_64.zip",
        },
    },
    "3.1.11": {
        "linux-aarch64": {
            "integrity": "sha256-13N5GPowN3eD3wx/a35r276pYHycLwte5uRzZHoxlKU=",
            "strip_prefix": "pandoc-3.1.11",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.11/pandoc-3.1.11-linux-arm64.tar.gz",
        },
        "linux-x86_64": {
            "integrity": "sha256-xXP8JbwIgIeb//mpKaKpxoNKbF5NfRZp+yPt3q7zeTc=",
            "strip_prefix": "pandoc-3.1.11",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.11/pandoc-3.1.11-linux-amd64.tar.gz",
        },
        "macos-aarch64": {
            "integrity": "sha256-d6zM/WjCX8FRrreSgrWHYqMUOCFFIuJTJdIZsUXrYcE=",
            "strip_prefix": "pandoc-3.1.11-arm64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.11/pandoc-3.1.11-arm64-macOS.zip",
        },
        "macos-x86_64": {
            "integrity": "sha256-VqM34I9+A8oGL71MSsGCUjw1Qp0UQdgmoTioydzCNUs=",
            "strip_prefix": "pandoc-3.1.11-x86_64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.11/pandoc-3.1.11-x86_64-macOS.zip",
        },
        "windows-x86_64": {
            "integrity": "sha256-7MNLxsoqBFdA9+R3FNWxlDuyDVCqxEGrLJ5Z5w3cryg=",
            "strip_prefix": "pandoc-3.1.11",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.11/pandoc-3.1.11-windows-x86_64.zip",
        },
    },
    "3.1.11.1": {
        "linux-aarch64": {
            "integrity": "sha256-Pq6SQg0+7oMOwSEme78ufzpsBmqljVmam3afUMSWfGc=",
            "strip_prefix": "pandoc-3.1.11.1",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.11.1/pandoc-3.1.11.1-linux-arm64.tar.gz",
        },
        "linux-x86_64": {
            "integrity": "sha256-B2NfaVMgHuJhv5DoIbj+NsBF5ab7rirmscISdxVDKUI=",
            "strip_prefix": "pandoc-3.1.11.1",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.11.1/pandoc-3.1.11.1-linux-amd64.tar.gz",
        },
        "macos-aarch64": {
            "integrity": "sha256-+jitkdjx8JVJrhaDCt46JmULA8uaKcaLQbVep/qwqi0=",
            "strip_prefix": "pandoc-3.1.11.1-arm64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.11.1/pandoc-3.1.11.1-arm64-macOS.zip",
        },
        "macos-x86_64": {
            "integrity": "sha256-ABjt3UiTiaxObPb0cRwa1JV0NhwEKC4HVAD60sAFAIQ=",
            "strip_prefix": "pandoc-3.1.11.1-x86_64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.11.1/pandoc-3.1.11.1-x86_64-macOS.zip",
        },
        "windows-x86_64": {
            "integrity": "sha256-Lb+Qi4yacw8yE4lsWgOsP5F2TC21zWE9qbS4zqC4ucY=",
            "strip_prefix": "pandoc-3.1.11.1",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.11.1/pandoc-3.1.11.1-windows-x86_64.zip",
        },
    },
    "3.1.12": {
        "linux-aarch64": {
            "integrity": "sha256-XieVK+593IjlYpv4YlIjO0GKvfj39myGxBKAVGmv1WA=",
            "strip_prefix": "pandoc-3.1.12",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.12/pandoc-3.1.12-linux-arm64.tar.gz",
        },
        "linux-x86_64": {
            "integrity": "sha256-4w0gzD+a76EXvyGD/nTPx8sEMjfVbrYycrgr92tTeZE=",
            "strip_prefix": "pandoc-3.1.12",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.12/pandoc-3.1.12-linux-amd64.tar.gz",
        },
        "macos-aarch64": {
            "integrity": "sha256-UmfOwjiJ5VpWM1YW5Zc0/7gDkcWh23w0HIPiC9nMdFw=",
            "strip_prefix": "pandoc-3.1.12-arm64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.12/pandoc-3.1.12-arm64-macOS.zip",
        },
        "macos-x86_64": {
            "integrity": "sha256-LKhn9SmHdl+hZ2/9nYsEugzy3Do8bBbEi1sFeHgiUJk=",
            "strip_prefix": "pandoc-3.1.12-x86_64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.12/pandoc-3.1.12-x86_64-macOS.zip",
        },
        "windows-x86_64": {
            "integrity": "sha256-KUCUfa2C00C3n2XxjsviNf6tZ0pUFBblyqAB2YRwPRQ=",
            "strip_prefix": "pandoc-3.1.12",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.12/pandoc-3.1.12-windows-x86_64.zip",
        },
    },
    "3.1.12.1": {
        "linux-aarch64": {
            "integrity": "sha256-uDBiggAuNEoXfi2FBHbG0gH2sqgi0sMBU8GZLqCY8ag=",
            "strip_prefix": "pandoc-3.1.12.1",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.12.1/pandoc-3.1.12.1-linux-arm64.tar.gz",
        },
        "linux-x86_64": {
            "integrity": "sha256-5qLLmSBPAl1DkeDJ71G6Er0eXCpUp9v7VwYY61EOFaY=",
            "strip_prefix": "pandoc-3.1.12.1",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.12.1/pandoc-3.1.12.1-linux-amd64.tar.gz",
        },
        "macos-aarch64": {
            "integrity": "sha256-Ew+fj0Y9UnssEWqmZwqx2fETJviL6Njd/METwDiPeAI=",
            "strip_prefix": "pandoc-3.1.12.1-arm64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.12.1/pandoc-3.1.12.1-arm64-macOS.zip",
        },
        "macos-x86_64": {
            "integrity": "sha256-0jzx2Ob5HDOJ980LlcDZT2mf/PwvEjVeYLFjoJa/Tg4=",
            "strip_prefix": "pandoc-3.1.12.1-x86_64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.12.1/pandoc-3.1.12.1-x86_64-macOS.zip",
        },
        "windows-x86_64": {
            "integrity": "sha256-8CyXbEd9x7wMO8/LAss1NPfqaI7Hy9ozLMig1b99KMg=",
            "strip_prefix": "pandoc-3.1.12.1",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.12.1/pandoc-3.1.12.1-windows-x86_64.zip",
        },
    },
    "3.1.12.2": {
        "linux-aarch64": {
            "integrity": "sha256-kDKyc67FoQULLl9yTIqdyvZXVAxo5E3Ed+yfw4rrwXM=",
            "strip_prefix": "pandoc-3.1.12.2",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.12.2/pandoc-3.1.12.2-linux-arm64.tar.gz",
        },
        "linux-x86_64": {
            "integrity": "sha256-QNpyUnf3YX0EX8dhsDdbO6CZDF0DqQjCB/7WG3jjSYY=",
            "strip_prefix": "pandoc-3.1.12.2",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.12.2/pandoc-3.1.12.2-linux-amd64.tar.gz",
        },
        "macos-aarch64": {
            "integrity": "sha256-HmUWWQcnQ9cwTWiR0jFweqm9eDMU41hyuU76waiXjy0=",
            "strip_prefix": "pandoc-3.1.12.2-arm64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.12.2/pandoc-3.1.12.2-arm64-macOS.zip",
        },
        "macos-x86_64": {
            "integrity": "sha256-9pPMWWGQU9p6ZgbuirgSZk7gM/Xvyojakgd8lgZvo3s=",
            "strip_prefix": "pandoc-3.1.12.2-x86_64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.12.2/pandoc-3.1.12.2-x86_64-macOS.zip",
        },
        "windows-x86_64": {
            "integrity": "sha256-hjFL0Ocjb0IhRzulSgfOZ3vC4elu1UYa1qVWsHI0oGE=",
            "strip_prefix": "pandoc-3.1.12.2",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.12.2/pandoc-3.1.12.2-windows-x86_64.zip",
        },
    },
    "3.1.12.3": {
        "linux-aarch64": {
            "integrity": "sha256-+ApPyhV/JK5pEs+L7UuS+i5eXFuY0Ke2dbyFNt62VgI=",
            "strip_prefix": "pandoc-3.1.12.3",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.12.3/pandoc-3.1.12.3-linux-arm64.tar.gz",
        },
        "linux-x86_64": {
            "integrity": "sha256-+A3xN6Bw4MBbf2o/jxeZEkus8VtX4FiQSIp/SfYU2gk=",
            "strip_prefix": "pandoc-3.1.12.3",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.12.3/pandoc-3.1.12.3-linux-amd64.tar.gz",
        },
        "macos-aarch64": {
            "integrity": "sha256-fGe6bkgaJ7zR2+0/TemC8u//angccGruJwAuRt7pXM4=",
            "strip_prefix": "pandoc-3.1.12.3-arm64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.12.3/pandoc-3.1.12.3-arm64-macOS.zip",
        },
        "macos-x86_64": {
            "integrity": "sha256-EIx63J/9v6l26uT3jTP+uamz8fu3UEUwbpzlD0k8YlI=",
            "strip_prefix": "pandoc-3.1.12.3-x86_64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.12.3/pandoc-3.1.12.3-x86_64-macOS.zip",
        },
        "windows-x86_64": {
            "integrity": "sha256-lIB/xc1a1IJyzfPw6eKjFTGCJGtE6YugLzWAtOrrV14=",
            "strip_prefix": "pandoc-3.1.12.3",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.12.3/pandoc-3.1.12.3-windows-x86_64.zip",
        },
    },
    "3.1.13": {
        "linux-aarch64": {
            "integrity": "sha256-Z4wJrEInyItJH251SR5tqHH9CNebjA8O43thHwGtPSU=",
            "strip_prefix": "pandoc-3.1.13",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.13/pandoc-3.1.13-linux-arm64.tar.gz",
        },
        "linux-x86_64": {
            "integrity": "sha256-21VsmM8gfS/dwIjRLS4vNn2UAXhNSj6RSwaPqJXc8/A=",
            "strip_prefix": "pandoc-3.1.13",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.13/pandoc-3.1.13-linux-amd64.tar.gz",
        },
        "macos-aarch64": {
            "integrity": "sha256-drFyLIHw+TSbbu8b84ciby6yd6ftR2QUdbnttTQDuYA=",
            "strip_prefix": "pandoc-3.1.13-arm64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.13/pandoc-3.1.13-arm64-macOS.zip",
        },
        "macos-x86_64": {
            "integrity": "sha256-MkmVZDq0JzvptS4b/Yj0kJ2SOPPa/UnLFoGoyjdDNr0=",
            "strip_prefix": "pandoc-3.1.13-x86_64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.13/pandoc-3.1.13-x86_64-macOS.zip",
        },
        "windows-x86_64": {
            "integrity": "sha256-NHslDoVdDLS/nn3No7VaK1va5YjmN6NjgQAIt1vlyoE=",
            "strip_prefix": "pandoc-3.1.13",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.13/pandoc-3.1.13-windows-x86_64.zip",
        },
    },
    "3.1.2": {
        "linux-aarch64": {
            "integrity": "sha256-isBM4K7a448Mn2S/5jSRA3jMMm0JEJI5WiFAp+yBnVQ=",
            "strip_prefix": "pandoc-3.1.2",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.2/pandoc-3.1.2-linux-arm64.tar.gz",
        },
        "linux-x86_64": {
            "integrity": "sha256-Thxgf35OkkP6Hh9bIIzU8dP2/QVdXYw5ugzcOGROHDU=",
            "strip_prefix": "pandoc-3.1.2",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.2/pandoc-3.1.2-linux-amd64.tar.gz",
        },
        "macos-aarch64": {
            "integrity": "sha256-qg6rbPEOXVTSVdaPj65H4I2gcVZaPSuNJCvimowfFGA=",
            "strip_prefix": "pandoc-3.1.2-arm64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.2/pandoc-3.1.2-arm64-macOS.zip",
        },
        "macos-x86_64": {
            "integrity": "sha256-csQ7HeMOZ9Oi9pv9aYgeX89u08JYPCrSIULDkNGF8LQ=",
            "strip_prefix": "pandoc-3.1.2-x86_64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.2/pandoc-3.1.2-x86_64-macOS.zip",
        },
        "windows-x86_64": {
            "integrity": "sha256-w1QfGjUgA0mJefJlnCVwrG3SJ+wSUzt1p2xNEJ510hg=",
            "strip_prefix": "pandoc-3.1.2",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.2/pandoc-3.1.2-windows-x86_64.zip",
        },
    },
    "3.1.3": {
        "linux-aarch64": {
            "integrity": "sha256-jFfOuOlI0mTN0SafUUHelmofk7G1CZ5lzbkqb+4x8WE=",
            "strip_prefix": "pandoc-3.1.3",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.3/pandoc-3.1.3-linux-arm64.tar.gz",
        },
        "linux-x86_64": {
            "integrity": "sha256-dLxDSQjk2Fiz7b/WJx0unkmUd4N+XfHWMN9OYvETgD0=",
            "strip_prefix": "pandoc-3.1.3",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.3/pandoc-3.1.3-linux-amd64.tar.gz",
        },
        "macos-aarch64": {
            "integrity": "sha256-3TOv50Rc9fuVrdiBvRG53qjlhtb7MPwydGF7MTIH+H4=",
            "strip_prefix": "pandoc-3.1.3-arm64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.3/pandoc-3.1.3-arm64-macOS.zip",
        },
        "macos-x86_64": {
            "integrity": "sha256-WKqCJ/y9Mj7EG95eEICPyzvvbK5tBRksgHqsb9hqbN8=",
            "strip_prefix": "pandoc-3.1.3-x86_64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.3/pandoc-3.1.3-x86_64-macOS.zip",
        },
        "windows-x86_64": {
            "integrity": "sha256-my1DnbMYimJNIS4cc0Yuu5dFNCfLRw3Ai7Mb8ShCkzc=",
            "strip_prefix": "pandoc-3.1.3",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.3/pandoc-3.1.3-windows-x86_64.zip",
        },
    },
    "3.1.4": {
        "linux-aarch64": {
            "integrity": "sha256-qaEKCFYSh5aEGG/RAxsEEOkj/UUBfESU2IAa0/hKkkA=",
            "strip_prefix": "pandoc-3.1.4",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.4/pandoc-3.1.4-linux-arm64.tar.gz",
        },
        "linux-x86_64": {
            "integrity": "sha256-BEbhMeEhYixosWLjfRwvdkXBgjGXteO/TAsmJ/yy4Uk=",
            "strip_prefix": "pandoc-3.1.4",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.4/pandoc-3.1.4-linux-amd64.tar.gz",
        },
        "macos-aarch64": {
            "integrity": "sha256-TU1GgVyugRgS6wayd5RltLnhdTLd11yRLuVg8L5n/BA=",
            "strip_prefix": "pandoc-3.1.4-arm64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.4/pandoc-3.1.4-arm64-macOS.zip",
        },
        "macos-x86_64": {
            "integrity": "sha256-9qbIX62NYig9ZDCWu5lnkI7nVcJX36/DHa8ya3k1TaU=",
            "strip_prefix": "pandoc-3.1.4-x86_64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.4/pandoc-3.1.4-x86_64-macOS.zip",
        },
        "windows-x86_64": {
            "integrity": "sha256-Z8qWhFqRtSyAFIjf0J6vS87VQw/a6fTg7IOWNbNrJp8=",
            "strip_prefix": "pandoc-3.1.4",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.4/pandoc-3.1.4-windows-x86_64.zip",
        },
    },
    "3.1.5": {
        "linux-aarch64": {
            "integrity": "sha256-qR7Su3dkwqTEDU4AbYyv5LlvgqZxYNfMKCZbhTo0Ygg=",
            "strip_prefix": "pandoc-3.1.5",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.5/pandoc-3.1.5-linux-arm64.tar.gz",
        },
        "linux-x86_64": {
            "integrity": "sha256-J2eAWYWAAACll7r32AtrvUOCp1SahQ4+6Abpn+hWFqc=",
            "strip_prefix": "pandoc-3.1.5",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.5/pandoc-3.1.5-linux-amd64.tar.gz",
        },
        "macos-aarch64": {
            "integrity": "sha256-IsqtjJXp90qMSyqq+KK4yp7EutnNpdYDKI8JOHp8D/4=",
            "strip_prefix": "pandoc-3.1.5-arm64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.5/pandoc-3.1.5-arm64-macOS.zip",
        },
        "macos-x86_64": {
            "integrity": "sha256-Pzw2NlCRDLnZqcgBpYrTaFS2eO6h4XSIgKOm+gtk57w=",
            "strip_prefix": "pandoc-3.1.5-x86_64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.5/pandoc-3.1.5-x86_64-macOS.zip",
        },
        "windows-x86_64": {
            "integrity": "sha256-Mt/Ihk1IwB/KZVeqJhrV0b+Vnnzt20IDgch6pqlNCcg=",
            "strip_prefix": "pandoc-3.1.5",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.5/pandoc-3.1.5-windows-x86_64.zip",
        },
    },
    "3.1.6": {
        "linux-aarch64": {
            "integrity": "sha256-bKeX81iwzASjuSCP8Zdahhv6cRDq+ogaqMAjrEBA4gg=",
            "strip_prefix": "pandoc-3.1.6",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.6/pandoc-3.1.6-linux-arm64.tar.gz",
        },
        "linux-x86_64": {
            "integrity": "sha256-buwODIXpfJCgK5GEyZPUvYSEJvs9dFLdwNYBQ2jF4/0=",
            "strip_prefix": "pandoc-3.1.6",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.6/pandoc-3.1.6-linux-amd64.tar.gz",
        },
        "macos-aarch64": {
            "integrity": "sha256-T6giiHR0zzoSwhW/neUpXwhM5OMPwSZ8lsaW7d2IqRI=",
            "strip_prefix": "pandoc-3.1.6-arm64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.6/pandoc-3.1.6-arm64-macOS.zip",
        },
        "macos-x86_64": {
            "integrity": "sha256-uhUPfhR5AWgVfvuHMk/+kw0wTJt4JKLpcSK7laz3bz4=",
            "strip_prefix": "pandoc-3.1.6-x86_64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.6/pandoc-3.1.6-x86_64-macOS.zip",
        },
        "windows-x86_64": {
            "integrity": "sha256-xswW3qtvC02S9LGJYU2kacG5mMq0L0I7JQwtNTZ9/98=",
            "strip_prefix": "pandoc-3.1.6",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.6/pandoc-3.1.6-windows-x86_64.zip",
        },
    },
    "3.1.6.1": {
        "linux-aarch64": {
            "integrity": "sha256-nT/plQ+FgSxdDISw7SeOS+QaGm1DUoEVxP6S3Q5gZek=",
            "strip_prefix": "pandoc-3.1.6.1",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.6.1/pandoc-3.1.6.1-linux-arm64.tar.gz",
        },
        "linux-x86_64": {
            "integrity": "sha256-wY1XRevYRcdeQSyj99okvfmfq5PJaJniJIedRYBNIh0=",
            "strip_prefix": "pandoc-3.1.6.1",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.6.1/pandoc-3.1.6.1-linux-amd64.tar.gz",
        },
        "macos-aarch64": {
            "integrity": "sha256-5mJoyJ+4ItITfLJjl2m8litSvmUxswkDYPJin+rzR4k=",
            "strip_prefix": "pandoc-3.1.6.1-arm64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.6.1/pandoc-3.1.6.1-arm64-macOS.zip",
        },
        "macos-x86_64": {
            "integrity": "sha256-/D52M6BUkwqvFPwjQIldlqNTfZ8sr5ibNa86UIY7K1A=",
            "strip_prefix": "pandoc-3.1.6.1-x86_64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.6.1/pandoc-3.1.6.1-x86_64-macOS.zip",
        },
        "windows-x86_64": {
            "integrity": "sha256-84f+ZhIhnwCCvndBnqC/g/7MVcztFJEPwuKshjN/OzU=",
            "strip_prefix": "pandoc-3.1.6.1",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.6.1/pandoc-3.1.6.1-windows-x86_64.zip",
        },
    },
    "3.1.6.2": {
        "linux-aarch64": {
            "integrity": "sha256-encCQo1fs0iq1AkDlyg7y8xTBRF73HS4JjcxvY8gBkQ=",
            "strip_prefix": "pandoc-3.1.6.2",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.6.2/pandoc-3.1.6.2-linux-arm64.tar.gz",
        },
        "linux-x86_64": {
            "integrity": "sha256-qchLdlmRiRVytLZ1JcGE1QHKv8dR5t4FTJArvHtB7lA=",
            "strip_prefix": "pandoc-3.1.6.2",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.6.2/pandoc-3.1.6.2-linux-amd64.tar.gz",
        },
        "macos-aarch64": {
            "integrity": "sha256-GkzngagIo39WWtLYpSpuuIoqcBOk3bSY/zkd8MoJ/dg=",
            "strip_prefix": "pandoc-3.1.6.2-arm64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.6.2/pandoc-3.1.6.2-arm64-macOS.zip",
        },
        "macos-x86_64": {
            "integrity": "sha256-v03uixzzb/zrlH0IFU2wry3XKPTQ+dLO8pDX1yIqMSI=",
            "strip_prefix": "pandoc-3.1.6.2-x86_64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.6.2/pandoc-3.1.6.2-x86_64-macOS.zip",
        },
        "windows-x86_64": {
            "integrity": "sha256-IbXk9x+5I5SKlSgorbb9hwSba2OPajXBjhu+xOpCUnk=",
            "strip_prefix": "pandoc-3.1.6.2",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.6.2/pandoc-3.1.6.2-windows-x86_64.zip",
        },
    },
    "3.1.7": {
        "linux-aarch64": {
            "integrity": "sha256-W5V0UIU3IFEeAMLqoFlmMJ6lkj9pPXr2AalEuLKzNR8=",
            "strip_prefix": "pandoc-3.1.7",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.7/pandoc-3.1.7-linux-arm64.tar.gz",
        },
        "linux-x86_64": {
            "integrity": "sha256-YyN/GjMzccqzJKh4DdE0VThtaKqStCiRdWEc/a0fMCw=",
            "strip_prefix": "pandoc-3.1.7",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.7/pandoc-3.1.7-linux-amd64.tar.gz",
        },
        "macos-aarch64": {
            "integrity": "sha256-OczcpRKpRit/nKWf1WqEo2csGZUA7OJ2GViQmNFEEcs=",
            "strip_prefix": "pandoc-3.1.7-arm64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.7/pandoc-3.1.7-arm64-macOS.zip",
        },
        "macos-x86_64": {
            "integrity": "sha256-wjRKAfKr26Gba688HSwei2o9zEMwzlC8vQFw6YW+OjU=",
            "strip_prefix": "pandoc-3.1.7-x86_64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.7/pandoc-3.1.7-x86_64-macOS.zip",
        },
        "windows-x86_64": {
            "integrity": "sha256-R3pcUaXgr+FkpWEHLnsUKK0DwAx4o4U8/Fj7qow2DgI=",
            "strip_prefix": "pandoc-3.1.7",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.7/pandoc-3.1.7-windows-x86_64.zip",
        },
    },
    "3.1.8": {
        "linux-aarch64": {
            "integrity": "sha256-DVdwWCeBBZok+iSiGqiIZX7L7mAVRbMzkIEWYFVXKtc=",
            "strip_prefix": "pandoc-3.1.8",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.8/pandoc-3.1.8-linux-arm64.tar.gz",
        },
        "linux-x86_64": {
            "integrity": "sha256-wHkjplMhtCRmWGNe3OUXrmV4q7ZTlr/5FP7vN7xIeEs=",
            "strip_prefix": "pandoc-3.1.8",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.8/pandoc-3.1.8-linux-amd64.tar.gz",
        },
        "macos-aarch64": {
            "integrity": "sha256-Bk1UGNLX71bbuMmmn4/2MTwawHnX36/ElSnG0VhCvL4=",
            "strip_prefix": "pandoc-3.1.8-arm64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.8/pandoc-3.1.8-arm64-macOS.zip",
        },
        "macos-x86_64": {
            "integrity": "sha256-cnVGNc80lZbpC2tMIn42PvRqMWouhsnUJL9SNXMlkAQ=",
            "strip_prefix": "pandoc-3.1.8-x86_64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.8/pandoc-3.1.8-x86_64-macOS.zip",
        },
        "windows-x86_64": {
            "integrity": "sha256-7WLkZt03ymJNXzlcqobY/2808+U8QQJZnd48qrW5ESE=",
            "strip_prefix": "pandoc-3.1.8",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.8/pandoc-3.1.8-windows-x86_64.zip",
        },
    },
    "3.1.9": {
        "linux-aarch64": {
            "integrity": "sha256-OTLxsHmTza47z6dSOo6xllQmnSww5OwW2TxCEZgP4no=",
            "strip_prefix": "pandoc-3.1.9",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.9/pandoc-3.1.9-linux-arm64.tar.gz",
        },
        "linux-x86_64": {
            "integrity": "sha256-TSzq5Ip/1Jq7TjkJiLC7EJmfvUcRD1Gvc3VaNZGNLGw=",
            "strip_prefix": "pandoc-3.1.9",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.9/pandoc-3.1.9-linux-amd64.tar.gz",
        },
        "macos-aarch64": {
            "integrity": "sha256-0/efybpNqEi3bp7fuHTNa8zpQwz0oQXDZGgoQFMQ1WI=",
            "strip_prefix": "pandoc-3.1.9-arm64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.9/pandoc-3.1.9-arm64-macOS.zip",
        },
        "macos-x86_64": {
            "integrity": "sha256-gg3XHA/1nDfhfeIqGf9no3Sg1D/e7mlSQVVgZ935m7w=",
            "strip_prefix": "pandoc-3.1.9-x86_64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.9/pandoc-3.1.9-x86_64-macOS.zip",
        },
        "windows-x86_64": {
            "integrity": "sha256-EettvlKGyeXtsMykQS59mexleOwEFYsLf+Eff9lmiOU=",
            "strip_prefix": "pandoc-3.1.9",
            "url": "https://github.com/jgm/pandoc/releases/download/3.1.9/pandoc-3.1.9-windows-x86_64.zip",
        },
    },
    "3.2": {
        "linux-aarch64": {
            "integrity": "sha256-k9bEFOWZTiVK7IQL6EKAFqcBZ8g1yjInN4IXk3vZoBo=",
            "strip_prefix": "pandoc-3.2",
            "url": "https://github.com/jgm/pandoc/releases/download/3.2/pandoc-3.2-linux-arm64.tar.gz",
        },
        "linux-x86_64": {
            "integrity": "sha256-6j+W3eVq4Vd8gRhGlLhXbY7+xS4WjOSabn3xRB9Cgok=",
            "strip_prefix": "pandoc-3.2",
            "url": "https://github.com/jgm/pandoc/releases/download/3.2/pandoc-3.2-linux-amd64.tar.gz",
        },
        "macos-aarch64": {
            "integrity": "sha256-l7cSBN2bGgj0B9djaV9U5x+WlCx0egS8FhAsnqtd46A=",
            "strip_prefix": "pandoc-3.2-arm64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.2/pandoc-3.2-arm64-macOS.zip",
        },
        "macos-x86_64": {
            "integrity": "sha256-DhHKAy+kUtafigagpKHCYDH/2V1vIxp4C3i9vI3TSIo=",
            "strip_prefix": "pandoc-3.2-x86_64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.2/pandoc-3.2-x86_64-macOS.zip",
        },
        "windows-x86_64": {
            "integrity": "sha256-hDlUYusI103z2+m7EpzjUI4+7D8prB9VVZwsWh80qL8=",
            "strip_prefix": "pandoc-3.2",
            "url": "https://github.com/jgm/pandoc/releases/download/3.2/pandoc-3.2-windows-x86_64.zip",
        },
    },
    "3.2.1": {
        "linux-aarch64": {
            "integrity": "sha256-I9MOf8wROqvYX8Qm1Lb5JPGw7rsGx+/DbpGI0Rf/WOw=",
            "strip_prefix": "pandoc-3.2.1",
            "url": "https://github.com/jgm/pandoc/releases/download/3.2.1/pandoc-3.2.1-linux-arm64.tar.gz",
        },
        "linux-x86_64": {
            "integrity": "sha256-NWiwqziqjH3c4IEvqfe+qKpD0WV8Xh6BbtkoB3GcDi0=",
            "strip_prefix": "pandoc-3.2.1",
            "url": "https://github.com/jgm/pandoc/releases/download/3.2.1/pandoc-3.2.1-linux-amd64.tar.gz",
        },
        "macos-aarch64": {
            "integrity": "sha256-uoEh1/i9CtGtGycbZptPSsEcH+bYAP5Fw8bOr77m+fE=",
            "strip_prefix": "pandoc-3.2.1-arm64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.2.1/pandoc-3.2.1-arm64-macOS.zip",
        },
        "macos-x86_64": {
            "integrity": "sha256-hMwJ+7iwcgdsuoKaSC7FqLRiKbgN2SF+qH3LIWbjgkU=",
            "strip_prefix": "pandoc-3.2.1-x86_64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.2.1/pandoc-3.2.1-x86_64-macOS.zip",
        },
        "windows-x86_64": {
            "integrity": "sha256-xs/HGwkqQsjSXAk2OQqiHXF2Ku4M7ucgv/HI4y01ID4=",
            "strip_prefix": "pandoc-3.2.1",
            "url": "https://github.com/jgm/pandoc/releases/download/3.2.1/pandoc-3.2.1-windows-x86_64.zip",
        },
    },
    "3.3": {
        "linux-aarch64": {
            "integrity": "sha256-rmF8zhuoB0U2GceRIoSa+6T1WAYQVvnhzA2hAYl5ZEM=",
            "strip_prefix": "pandoc-3.3",
            "url": "https://github.com/jgm/pandoc/releases/download/3.3/pandoc-3.3-linux-arm64.tar.gz",
        },
        "linux-x86_64": {
            "integrity": "sha256-DJfQPoWmWzZvsczZ2zKoDBDuuubh3DbuWEWPUpTVhVY=",
            "strip_prefix": "pandoc-3.3",
            "url": "https://github.com/jgm/pandoc/releases/download/3.3/pandoc-3.3-linux-amd64.tar.gz",
        },
        "macos-aarch64": {
            "integrity": "sha256-n5d3TWzWo1EBIv7WvNBbBg4X9dLbXPjt7E2WxnDVZg0=",
            "strip_prefix": "pandoc-3.3-arm64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.3/pandoc-3.3-arm64-macOS.zip",
        },
        "macos-x86_64": {
            "integrity": "sha256-GpvHCqowbTJ0+dhtmjplbsHjZtwJ8C/R6ODKsP+8Alk=",
            "strip_prefix": "pandoc-3.3-x86_64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.3/pandoc-3.3-x86_64-macOS.zip",
        },
        "windows-x86_64": {
            "integrity": "sha256-BbR1OfCcZf2UzioXQUEoBQdK52RHcmei/5ws3o6n/o0=",
            "strip_prefix": "pandoc-3.3",
            "url": "https://github.com/jgm/pandoc/releases/download/3.3/pandoc-3.3-windows-x86_64.zip",
        },
    },
    "3.4": {
        "linux-aarch64": {
            "integrity": "sha256-pm7AHxJIfe8o7tIqzFqP5MfIaTJSkapAN7M+GRXyVo0=",
            "strip_prefix": "pandoc-3.4",
            "url": "https://github.com/jgm/pandoc/releases/download/3.4/pandoc-3.4-linux-arm64.tar.gz",
        },
        "linux-x86_64": {
            "integrity": "sha256-9vRsxhq/O6ywv2EvTYC1hmJcEM9kpLRWhT/TWMtMcxk=",
            "strip_prefix": "pandoc-3.4",
            "url": "https://github.com/jgm/pandoc/releases/download/3.4/pandoc-3.4-linux-amd64.tar.gz",
        },
        "macos-aarch64": {
            "integrity": "sha256-K8SO8VLVQEzH1bmO4B8Rr4vZHlA6boiNJTe9JhpXjQI=",
            "strip_prefix": "pandoc-3.4-arm64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.4/pandoc-3.4-arm64-macOS.zip",
        },
        "macos-x86_64": {
            "integrity": "sha256-+zQiE84Wr0qBVl8fEGqAhXT5k5AKyRSlc3ZJuoztsrM=",
            "strip_prefix": "pandoc-3.4-x86_64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.4/pandoc-3.4-x86_64-macOS.zip",
        },
        "windows-x86_64": {
            "integrity": "sha256-JoWM9ZwFez08oy6c0vvR9QmQrcG/sgqcjfuTaqzDYQ4=",
            "strip_prefix": "pandoc-3.4",
            "url": "https://github.com/jgm/pandoc/releases/download/3.4/pandoc-3.4-windows-x86_64.zip",
        },
    },
    "3.5": {
        "linux-aarch64": {
            "integrity": "sha256-G9liCbsWoMCJDR9V6sXUtvqsl1vuIL9wPfJj8ECPK1E=",
            "strip_prefix": "pandoc-3.5",
            "url": "https://github.com/jgm/pandoc/releases/download/3.5/pandoc-3.5-linux-arm64.tar.gz",
        },
        "linux-x86_64": {
            "integrity": "sha256-pGtEitnn5b2JigYGoqZ6y/S8dxSyTcaJMemkfXuAcBU=",
            "strip_prefix": "pandoc-3.5",
            "url": "https://github.com/jgm/pandoc/releases/download/3.5/pandoc-3.5-linux-amd64.tar.gz",
        },
        "macos-aarch64": {
            "integrity": "sha256-CNVxoVXUm21zCDlKyQxgnjWYLxng9lhE1C04+ZJxAKc=",
            "strip_prefix": "pandoc-3.5-arm64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.5/pandoc-3.5-arm64-macOS.zip",
        },
        "macos-x86_64": {
            "integrity": "sha256-BBRN08yhsbhDtAJK8vYXyRjsL/W/9SNOOwGVhY73FUk=",
            "strip_prefix": "pandoc-3.5-x86_64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.5/pandoc-3.5-x86_64-macOS.zip",
        },
        "windows-x86_64": {
            "integrity": "sha256-iH6YDiIo2NRaQxk26LxicKUMyaWk7H5iBko6XeZCO3E=",
            "strip_prefix": "pandoc-3.5",
            "url": "https://github.com/jgm/pandoc/releases/download/3.5/pandoc-3.5-windows-x86_64.zip",
        },
    },
    "3.6": {
        "linux-aarch64": {
            "integrity": "sha256-Q3dzGgyJYZOuq3VzT9WWXCEjJjj94RfzDk1ZFwBAXg8=",
            "strip_prefix": "pandoc-3.6",
            "url": "https://github.com/jgm/pandoc/releases/download/3.6/pandoc-3.6-linux-arm64.tar.gz",
        },
        "linux-x86_64": {
            "integrity": "sha256-jjcCsZX3VBLkJd9G+PPwgkG2aiszq72eBO2lAb/ehgw=",
            "strip_prefix": "pandoc-3.6",
            "url": "https://github.com/jgm/pandoc/releases/download/3.6/pandoc-3.6-linux-amd64.tar.gz",
        },
        "macos-aarch64": {
            "integrity": "sha256-eP7a5CZoLym9PA2uUfdyWXOvvAEVM7NYAmVw6lkPx4U=",
            "strip_prefix": "pandoc-3.6-arm64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.6/pandoc-3.6-arm64-macOS.zip",
        },
        "macos-x86_64": {
            "integrity": "sha256-I6KEyo+ibG07XtMkmlu4K1kpuexjYzxMFW3Lv3V67e8=",
            "strip_prefix": "pandoc-3.6-x86_64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.6/pandoc-3.6-x86_64-macOS.zip",
        },
        "windows-x86_64": {
            "integrity": "sha256-BnMre5bTuZ9xG6G/JPKJ/LW8lWEZK9wb2VFMF8iqLCA=",
            "strip_prefix": "pandoc-3.6",
            "url": "https://github.com/jgm/pandoc/releases/download/3.6/pandoc-3.6-windows-x86_64.zip",
        },
    },
    "3.6.1": {
        "linux-aarch64": {
            "integrity": "sha256-7dJ4xvWTel6QiPPXj8A5q8DYc0gmStP3xRuhJL9YDo0=",
            "strip_prefix": "pandoc-3.6.1",
            "url": "https://github.com/jgm/pandoc/releases/download/3.6.1/pandoc-3.6.1-linux-arm64.tar.gz",
        },
        "linux-x86_64": {
            "integrity": "sha256-cCQaPo8MKjAQPXlUSAAl5UftT0C4zc5nTN8L6fAr1aM=",
            "strip_prefix": "pandoc-3.6.1",
            "url": "https://github.com/jgm/pandoc/releases/download/3.6.1/pandoc-3.6.1-linux-amd64.tar.gz",
        },
        "macos-aarch64": {
            "integrity": "sha256-2jjfgO+P0yfcxsyDOCaXrVluxiGgXXuD9o96vhTldy4=",
            "strip_prefix": "pandoc-3.6.1-arm64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.6.1/pandoc-3.6.1-arm64-macOS.zip",
        },
        "macos-x86_64": {
            "integrity": "sha256-DzbgRN0Ivpbcc0IsbP+2FTWmH2m/urlLOnWnzTeo8gs=",
            "strip_prefix": "pandoc-3.6.1-x86_64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.6.1/pandoc-3.6.1-x86_64-macOS.zip",
        },
        "windows-x86_64": {
            "integrity": "sha256-qfKzDhUe/2wYAXFRr3qraPeHXokv+Ymdrcl3CvIosqI=",
            "strip_prefix": "pandoc-3.6.1",
            "url": "https://github.com/jgm/pandoc/releases/download/3.6.1/pandoc-3.6.1-windows-x86_64.zip",
        },
    },
    "3.6.2": {
        "linux-aarch64": {
            "integrity": "sha256-7q9OZEl5S3gZ3lLBrGxVodS0n6pu3TJD2TATRp9wrgA=",
            "strip_prefix": "pandoc-3.6.2",
            "url": "https://github.com/jgm/pandoc/releases/download/3.6.2/pandoc-3.6.2-linux-arm64.tar.gz",
        },
        "linux-x86_64": {
            "integrity": "sha256-8Rs/IVSfI+PVuZ36y5ZWDATC92An7beHxNZVGEms9Uo=",
            "strip_prefix": "pandoc-3.6.2",
            "url": "https://github.com/jgm/pandoc/releases/download/3.6.2/pandoc-3.6.2-linux-amd64.tar.gz",
        },
        "macos-aarch64": {
            "integrity": "sha256-rE4AkOpF/R2MMhM6WODbtrN0l1zNXRrKFDHqcD4/qcw=",
            "strip_prefix": "pandoc-3.6.2-arm64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.6.2/pandoc-3.6.2-arm64-macOS.zip",
        },
        "macos-x86_64": {
            "integrity": "sha256-c43hwmbvEOyw+FgUaEU6smIl/pSekD1xcIHC8z2xiGc=",
            "strip_prefix": "pandoc-3.6.2-x86_64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.6.2/pandoc-3.6.2-x86_64-macOS.zip",
        },
        "windows-x86_64": {
            "integrity": "sha256-hPRTswiP5PLMLpBSZuqAv7/P7AwQhV91uvX80dMoXfk=",
            "strip_prefix": "pandoc-3.6.2",
            "url": "https://github.com/jgm/pandoc/releases/download/3.6.2/pandoc-3.6.2-windows-x86_64.zip",
        },
    },
    "3.6.3": {
        "linux-aarch64": {
            "integrity": "sha256-TndMsb225WvFW463kgC9mqajmQWgTs2nJn9RSRFvCIE=",
            "strip_prefix": "pandoc-3.6.3",
            "url": "https://github.com/jgm/pandoc/releases/download/3.6.3/pandoc-3.6.3-linux-arm64.tar.gz",
        },
        "linux-x86_64": {
            "integrity": "sha256-0EyVwTggL4fWsArBmqPdh0xoH2Cp/rO1XHT3ZNbRoX0=",
            "strip_prefix": "pandoc-3.6.3",
            "url": "https://github.com/jgm/pandoc/releases/download/3.6.3/pandoc-3.6.3-linux-amd64.tar.gz",
        },
        "macos-aarch64": {
            "integrity": "sha256-HXbNdrcD/3WPkPaSm9X2NLxQ/HatN1qdGaXTZc2CM/w=",
            "strip_prefix": "pandoc-3.6.3-arm64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.6.3/pandoc-3.6.3-arm64-macOS.zip",
        },
        "macos-x86_64": {
            "integrity": "sha256-z2uFQ9BPQWLr5OOx/wBgGOo5XrPtj8l7iA12Djvgoak=",
            "strip_prefix": "pandoc-3.6.3-x86_64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.6.3/pandoc-3.6.3-x86_64-macOS.zip",
        },
        "windows-x86_64": {
            "integrity": "sha256-ox3FsUojXvofLPED9x9lbut2zhtFjSLSTzkMZttyJPE=",
            "strip_prefix": "pandoc-3.6.3",
            "url": "https://github.com/jgm/pandoc/releases/download/3.6.3/pandoc-3.6.3-windows-x86_64.zip",
        },
    },
    "3.6.4": {
        "linux-aarch64": {
            "integrity": "sha256-rVz2P+BCA4jZ7FE/AtA+BhR3t4bRGjKBZNzorXOHuL0=",
            "strip_prefix": "pandoc-3.6.4",
            "url": "https://github.com/jgm/pandoc/releases/download/3.6.4/pandoc-3.6.4-linux-arm64.tar.gz",
        },
        "linux-x86_64": {
            "integrity": "sha256-Xe9uH/U145e+zOKS7pd2epRzBhULn7FIgAO2esNBfF4=",
            "strip_prefix": "pandoc-3.6.4",
            "url": "https://github.com/jgm/pandoc/releases/download/3.6.4/pandoc-3.6.4-linux-amd64.tar.gz",
        },
        "macos-aarch64": {
            "integrity": "sha256-iK8X8Yha+ssl9wzkyMREKP622oYLbPaQ4w2neZhFbH8=",
            "strip_prefix": "pandoc-3.6.4-arm64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.6.4/pandoc-3.6.4-arm64-macOS.zip",
        },
        "macos-x86_64": {
            "integrity": "sha256-NXiftK/GEma5VANQWYIN1UaxDY8F/vNqjerf+u3/wrg=",
            "strip_prefix": "pandoc-3.6.4-x86_64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.6.4/pandoc-3.6.4-x86_64-macOS.zip",
        },
        "windows-x86_64": {
            "integrity": "sha256-qeX+s9VtL7Dj52XRwzuO5rcuaWPX3jFQTt7sjNG+NLE=",
            "strip_prefix": "pandoc-3.6.4",
            "url": "https://github.com/jgm/pandoc/releases/download/3.6.4/pandoc-3.6.4-windows-x86_64.zip",
        },
    },
    "3.7": {
        "linux-aarch64": {
            "integrity": "sha256-WTrLHuPMilOCm3cEs7CWPGDEK77gxBJp8pOVy74o/CU=",
            "strip_prefix": "pandoc-3.7",
            "url": "https://github.com/jgm/pandoc/releases/download/3.7/pandoc-3.7-linux-arm64.tar.gz",
        },
        "linux-x86_64": {
            "integrity": "sha256-jm3MAsOxSw29U3RGtdMvC7ShVQOtgTjRXSIAb5dIelM=",
            "strip_prefix": "pandoc-3.7",
            "url": "https://github.com/jgm/pandoc/releases/download/3.7/pandoc-3.7-linux-amd64.tar.gz",
        },
        "macos-aarch64": {
            "integrity": "sha256-vGQ4cPACxLB+rWiuFUKIZexvqYL2ggnUQrSiE0xP9+w=",
            "strip_prefix": "pandoc-3.7-arm64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.7/pandoc-3.7-arm64-macOS.zip",
        },
        "macos-x86_64": {
            "integrity": "sha256-s8273HipuVVPRsOxwnEfFpEY5R4gmSv+PYgulXPlKwU=",
            "strip_prefix": "pandoc-3.7-x86_64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.7/pandoc-3.7-x86_64-macOS.zip",
        },
        "windows-x86_64": {
            "integrity": "sha256-14i0N2cNNp2KA09KeRt4jLC7nZLOPKw1on6TgSKtD74=",
            "strip_prefix": "pandoc-3.7",
            "url": "https://github.com/jgm/pandoc/releases/download/3.7/pandoc-3.7-windows-x86_64.zip",
        },
    },
    "3.7.0.1": {
        "linux-aarch64": {
            "integrity": "sha256-0EW4GZj5Mt+ciHagfbAcys9C4hFzhAKcRtW4O0bvceU=",
            "strip_prefix": "pandoc-3.7.0.1",
            "url": "https://github.com/jgm/pandoc/releases/download/3.7.0.1/pandoc-3.7.0.1-linux-arm64.tar.gz",
        },
        "linux-x86_64": {
            "integrity": "sha256-c4JBAME536WRekWXRRPW29rwNlhCQADd74xLDN58zog=",
            "strip_prefix": "pandoc-3.7.0.1",
            "url": "https://github.com/jgm/pandoc/releases/download/3.7.0.1/pandoc-3.7.0.1-linux-amd64.tar.gz",
        },
        "macos-aarch64": {
            "integrity": "sha256-NArQWrZeaxBo8+uH/wV9PCBRiDlltJ46K0HeUKrbZfg=",
            "strip_prefix": "pandoc-3.7.0.1-arm64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.7.0.1/pandoc-3.7.0.1-arm64-macOS.zip",
        },
        "macos-x86_64": {
            "integrity": "sha256-tT0V6w27LpsWee+h9OMlHJVBhjxj/zcMCgPuNjKY6Co=",
            "strip_prefix": "pandoc-3.7.0.1-x86_64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.7.0.1/pandoc-3.7.0.1-x86_64-macOS.zip",
        },
        "windows-x86_64": {
            "integrity": "sha256-1pXix6Hp6lDZ4sq1AiocJ/g9Fgy1sb3rr9pBEoG+dNE=",
            "strip_prefix": "pandoc-3.7.0.1",
            "url": "https://github.com/jgm/pandoc/releases/download/3.7.0.1/pandoc-3.7.0.1-windows-x86_64.zip",
        },
    },
    "3.7.0.2": {
        "linux-aarch64": {
            "integrity": "sha256-TvKZf/D6f4atpaIXci9PcyKT44UYtEQuzszhZii9DkQ=",
            "strip_prefix": "pandoc-3.7.0.2",
            "url": "https://github.com/jgm/pandoc/releases/download/3.7.0.2/pandoc-3.7.0.2-linux-arm64.tar.gz",
        },
        "linux-x86_64": {
            "integrity": "sha256-j49n/dVAtlGTJrCsSdXFXF1dFeQ5IOgKCG4CyK/4Mmg=",
            "strip_prefix": "pandoc-3.7.0.2",
            "url": "https://github.com/jgm/pandoc/releases/download/3.7.0.2/pandoc-3.7.0.2-linux-amd64.tar.gz",
        },
        "macos-aarch64": {
            "integrity": "sha256-ZqV5vYqug94LvrpDkAlTsHWmo8qqfRv8GRc+j5XS6hc=",
            "strip_prefix": "pandoc-3.7.0.2-arm64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.7.0.2/pandoc-3.7.0.2-arm64-macOS.zip",
        },
        "macos-x86_64": {
            "integrity": "sha256-VJWvLFSL1J/gDCin9traoTSOYzi5I2jT1uKf0+FgYdE=",
            "strip_prefix": "pandoc-3.7.0.2-x86_64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.7.0.2/pandoc-3.7.0.2-x86_64-macOS.zip",
        },
        "windows-x86_64": {
            "integrity": "sha256-FPpizznJMJWIGOzq0qav6T9uZAy09RD/5vm0htzguhM=",
            "strip_prefix": "pandoc-3.7.0.2",
            "url": "https://github.com/jgm/pandoc/releases/download/3.7.0.2/pandoc-3.7.0.2-windows-x86_64.zip",
        },
    },
    "3.8": {
        "linux-aarch64": {
            "integrity": "sha256-h8rHsrAklcBTP3UZO0CDfFDFwxPZBbGYKcch1hegc7k=",
            "strip_prefix": "pandoc-3.8",
            "url": "https://github.com/jgm/pandoc/releases/download/3.8/pandoc-3.8-linux-arm64.tar.gz",
        },
        "linux-x86_64": {
            "integrity": "sha256-GgNcH30pXDU/YURh+kvBPXA8DoZTh9RDQdFVbXA95Zo=",
            "strip_prefix": "pandoc-3.8",
            "url": "https://github.com/jgm/pandoc/releases/download/3.8/pandoc-3.8-linux-amd64.tar.gz",
        },
        "macos-aarch64": {
            "integrity": "sha256-fPqgSleBY5fdZJj9UK2gG96wT+76tzfaN9ST+zATFTM=",
            "strip_prefix": "pandoc-3.8-arm64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.8/pandoc-3.8-arm64-macOS.zip",
        },
        "macos-x86_64": {
            "integrity": "sha256-B6f7fbY0ZxDzybBubrDOSaZq+g0ZaaoBWOyxTZ6uyyA=",
            "strip_prefix": "pandoc-3.8-x86_64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.8/pandoc-3.8-x86_64-macOS.zip",
        },
        "windows-x86_64": {
            "integrity": "sha256-PHLumWbSo167WYc5Z+SW9f50XBXPnoJZR9x0XRmza60=",
            "strip_prefix": "pandoc-3.8",
            "url": "https://github.com/jgm/pandoc/releases/download/3.8/pandoc-3.8-windows-x86_64.zip",
        },
    },
    "3.8.1": {
        "linux-aarch64": {
            "integrity": "sha256-szPdgwF80Mo3SBRsBRA0//TrCwVnfkfxrqNqpSQP07U=",
            "strip_prefix": "pandoc-3.8.1",
            "url": "https://github.com/jgm/pandoc/releases/download/3.8.1/pandoc-3.8.1-linux-arm64.tar.gz",
        },
        "linux-x86_64": {
            "integrity": "sha256-LZCGotAeeId5fgzE8HqPpgCLNPiWEt2SFBksAAirWKs=",
            "strip_prefix": "pandoc-3.8.1",
            "url": "https://github.com/jgm/pandoc/releases/download/3.8.1/pandoc-3.8.1-linux-amd64.tar.gz",
        },
        "macos-aarch64": {
            "integrity": "sha256-4f5cfHfmgLIlijCe97O3xqIRuSA8gzLKiClfRih+/Uc=",
            "strip_prefix": "pandoc-3.8.1-arm64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.8.1/pandoc-3.8.1-arm64-macOS.zip",
        },
        "macos-x86_64": {
            "integrity": "sha256-t7Fddwc4g2xAxoq1HAog1MT6kfsKzohstSz/gzTAPq0=",
            "strip_prefix": "pandoc-3.8.1-x86_64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.8.1/pandoc-3.8.1-x86_64-macOS.zip",
        },
        "windows-x86_64": {
            "integrity": "sha256-XJ2abXdMrl7LIqF1kbDPU1VWX/7qt0bYtn7hlKLVqEk=",
            "strip_prefix": "pandoc-3.8.1",
            "url": "https://github.com/jgm/pandoc/releases/download/3.8.1/pandoc-3.8.1-windows-x86_64.zip",
        },
    },
    "3.8.2": {
        "linux-aarch64": {
            "integrity": "sha256-iYtcH2vKuKYCU8yhAn5DR276ItHOmSMruVjNEYA7y5A=",
            "strip_prefix": "pandoc-3.8.2",
            "url": "https://github.com/jgm/pandoc/releases/download/3.8.2/pandoc-3.8.2-linux-arm64.tar.gz",
        },
        "linux-x86_64": {
            "integrity": "sha256-MlLF/YI0kl9Glz9PF/hSzNpkd3oMYx1XNYYcfrTWkTI=",
            "strip_prefix": "pandoc-3.8.2",
            "url": "https://github.com/jgm/pandoc/releases/download/3.8.2/pandoc-3.8.2-linux-amd64.tar.gz",
        },
        "macos-aarch64": {
            "integrity": "sha256-AlA+6RWP5lRCci2IGMN4M+1HZtlwzgKQtp4I0FH2Yo0=",
            "strip_prefix": "pandoc-3.8.2-arm64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.8.2/pandoc-3.8.2-arm64-macOS.zip",
        },
        "macos-x86_64": {
            "integrity": "sha256-6C8kHs1VW3mMzqsnMRgz2ao6R0WD9nzCczkoAui24OA=",
            "strip_prefix": "pandoc-3.8.2-x86_64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.8.2/pandoc-3.8.2-x86_64-macOS.zip",
        },
        "windows-x86_64": {
            "integrity": "sha256-O83Fx3rlvVQGEAwsS/3I0X1eTXVq018XkaqAUoLcsz4=",
            "strip_prefix": "pandoc-3.8.2",
            "url": "https://github.com/jgm/pandoc/releases/download/3.8.2/pandoc-3.8.2-windows-x86_64.zip",
        },
    },
    "3.8.2.1": {
        "linux-aarch64": {
            "integrity": "sha256-hS6JjCSQ+oQK51qLavimydbWO3fvFwwy7DoXlYRk2Sk=",
            "strip_prefix": "pandoc-3.8.2.1",
            "url": "https://github.com/jgm/pandoc/releases/download/3.8.2.1/pandoc-3.8.2.1-linux-arm64.tar.gz",
        },
        "linux-x86_64": {
            "integrity": "sha256-s2KBXiHYrTYpwSSqkrr1RVjaCGrXI3S09v3Ze58ydbA=",
            "strip_prefix": "pandoc-3.8.2.1",
            "url": "https://github.com/jgm/pandoc/releases/download/3.8.2.1/pandoc-3.8.2.1-linux-amd64.tar.gz",
        },
        "macos-aarch64": {
            "integrity": "sha256-R26aBYgmZ+5eqpH0tRPkQf8GyewnAPAFvEJpAMyugZA=",
            "strip_prefix": "pandoc-3.8.2.1-arm64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.8.2.1/pandoc-3.8.2.1-arm64-macOS.zip",
        },
        "macos-x86_64": {
            "integrity": "sha256-wmZs+iFSYu/9hdnhgcTf++2U+BiW5w1AQCoDduDUIq0=",
            "strip_prefix": "pandoc-3.8.2.1-x86_64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.8.2.1/pandoc-3.8.2.1-x86_64-macOS.zip",
        },
        "windows-x86_64": {
            "integrity": "sha256-3tc4kFZ65xuUXIs2uLM/ibXtc1epFWojNEW0b5KlvII=",
            "strip_prefix": "pandoc-3.8.2.1",
            "url": "https://github.com/jgm/pandoc/releases/download/3.8.2.1/pandoc-3.8.2.1-windows-x86_64.zip",
        },
    },
    "3.8.3": {
        "linux-aarch64": {
            "integrity": "sha256-FmpaNzh+sQvUxPJCqBCb7vdVrB6NTrA5xrXr0dkY2Nc=",
            "strip_prefix": "pandoc-3.8.3",
            "url": "https://github.com/jgm/pandoc/releases/download/3.8.3/pandoc-3.8.3-linux-arm64.tar.gz",
        },
        "linux-x86_64": {
            "integrity": "sha256-wiT6uJ+CfTYjOA7LfBB4wWPHachJoUrCfo07+7kUybQ=",
            "strip_prefix": "pandoc-3.8.3",
            "url": "https://github.com/jgm/pandoc/releases/download/3.8.3/pandoc-3.8.3-linux-amd64.tar.gz",
        },
        "macos-aarch64": {
            "integrity": "sha256-Pq6zvRCYKuy6XddhWHRaT4Ba+zmrcqUZu6JTPJjOAC0=",
            "strip_prefix": "pandoc-3.8.3-arm64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.8.3/pandoc-3.8.3-arm64-macOS.zip",
        },
        "macos-x86_64": {
            "integrity": "sha256-ki41wCENfKIO6TJ4ETYdbX8O8K3aCJ4OdMs3VsPXE/k=",
            "strip_prefix": "pandoc-3.8.3-x86_64",
            "url": "https://github.com/jgm/pandoc/releases/download/3.8.3/pandoc-3.8.3-x86_64-macOS.zip",
        },
        "windows-x86_64": {
            "integrity": "sha256-p3wUB4pcTG45bV9cA/SEnv9KhYQUu55pVguzVSjL9Xo=",
            "strip_prefix": "pandoc-3.8.3",
            "url": "https://github.com/jgm/pandoc/releases/download/3.8.3/pandoc-3.8.3-windows-x86_64.zip",
        },
    },
}
