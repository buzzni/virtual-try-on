export const metadata = {
  title: 'Buzzni VTO',
  description: 'Virtual Try-On',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  )
}
