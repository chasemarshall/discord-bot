import './globals.css';

export const metadata = {
  title: 'Clearway Discord Bot',
  description: 'Clearway Discord Bot frontend',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
