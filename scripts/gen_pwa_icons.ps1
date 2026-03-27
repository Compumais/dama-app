$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.Drawing

function New-Icon {
    param(
        [Parameter(Mandatory = $true)][int]$Size,
        [Parameter(Mandatory = $true)][string]$Path
    )

    $bmp = New-Object System.Drawing.Bitmap $Size, $Size
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias

    $rect = New-Object System.Drawing.Rectangle 0, 0, $Size, $Size
    $c1 = [System.Drawing.ColorTranslator]::FromHtml("#28554b")
    $c2 = [System.Drawing.ColorTranslator]::FromHtml("#c96f32")
    $bg = New-Object System.Drawing.Drawing2D.LinearGradientBrush $rect, $c1, $c2, 45
    $g.FillRectangle($bg, 0, 0, $Size, $Size)

    $penWidth = [Math]::Max(2, [int]($Size * 0.02))
    $pen = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(55, 255, 255, 255)), $penWidth
    $boxX = [int]($Size * 0.18)
    $boxY = [int]($Size * 0.18)
    $boxW = [int]($Size * 0.64)
    $boxH = [int]($Size * 0.64)
    $g.DrawRectangle($pen, $boxX, $boxY, $boxW, $boxH)

    $fontSize = [Math]::Max(18, [int]($Size * 0.13))
    $font = New-Object System.Drawing.Font "Segoe UI", $fontSize, ([System.Drawing.FontStyle]::Bold)
    $sf = New-Object System.Drawing.StringFormat
    $sf.Alignment = [System.Drawing.StringAlignment]::Center
    $sf.LineAlignment = [System.Drawing.StringAlignment]::Center
    $textRect = New-Object System.Drawing.RectangleF 0, ([float]($Size * 0.62)), $Size, ([float]($Size * 0.30))
    $g.DrawString("DAMA", $font, [System.Drawing.Brushes]::White, $textRect, $sf)

    $g.Dispose()
    $bmp.Save($Path, [System.Drawing.Imaging.ImageFormat]::Png)
    $bmp.Dispose()
}

New-Icon -Size 192 -Path "app\static\img\icon-192.png"
New-Icon -Size 512 -Path "app\static\img\icon-512.png"
Write-Output "Generated icons."

