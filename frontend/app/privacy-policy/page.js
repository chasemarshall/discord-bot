// 📄 app/privacy-policy/page.js
import Link from 'next/link';
import { Home } from 'lucide-react';

export const metadata = {
  title: 'Privacy Policy - Clearway Discord Bot',
  description: "Clearway privacy policy - we don't collect any user data",
}

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-black text-white">
      {/* Navigation */}
      <nav className="border-b border-gray-800 bg-black/50 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-4xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <Link href="/" className="flex items-center space-x-3 hover:opacity-80 transition-opacity">
              <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-blue-500 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">C</span>
              </div>
              <span className="text-xl font-semibold">Clearway</span>
            </Link>
            <div className="flex items-center space-x-6">
              <Link href="/" className="text-gray-400 hover:text-white transition-colors flex items-center space-x-1">
                <Home className="w-4 h-4" />
                <span>Home</span>
              </Link>
              <Link href="/tos" className="text-gray-400 hover:text-white transition-colors">
                Terms
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-6 py-16">
        <div className="mb-12">
          <h1 className="text-4xl font-bold mb-4">Privacy Policy</h1>
          <p className="text-gray-400">Last updated: August 25, 2024</p>
        </div>

        <div className="prose prose-invert max-w-none">
            <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-6 mb-8">
            <h3 className="text-green-400 font-semibold mb-2">TL;DR - We Can See It, But We Don't Save It</h3>
            <p className="text-sm text-gray-300">Clearway can access Discord server information like messages and member details (just like any bot), but we don't store, log, or track any of it. Everything is processed in real-time and immediately discarded.</p>
          </div>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">What We Can Access vs. What We Store</h2>
            <p className="text-gray-300 mb-4">
              Like all Discord bots, Clearway can access certain information when operating in your server. However, we follow a strict policy of not storing or logging any of this data:
            </p>
            
            <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-6 mb-6">
              <h4 className="text-blue-400 font-semibold mb-3">Information We Can Access (But Don't Store):</h4>
              <ul className="text-gray-300 space-y-1 text-sm">
                <li>• Message content (when mentioned or for commands)</li>
                <li>• User IDs, usernames, nicknames, and display names</li>
                <li>• Server member lists and their roles</li>
                <li>• User online status and activity (what they're playing/doing)</li>
                <li>• Permission changes and role modifications</li>
                <li>• Basic server information (name, channels, settings)</li>
              </ul>
            </div>

            <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-6">
              <h4 className="text-green-400 font-semibold mb-3">What We Actually Do:</h4>
              <ul className="text-gray-300 space-y-1 text-sm">
                <li>• Process commands in real-time and immediately discard the data</li>
                <li>• Never log, store, or retain any user information</li>
                <li>• Don't create databases or files with your data</li>
                <li>• Don't track usage patterns or analytics</li>
                <li>• Don't monitor conversations or member activity</li>
              </ul>
            </div>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">How Commands Work</h2>
            <p className="text-gray-300 mb-4">
              When you use Clearway's commands, the bot processes your requests in real-time and returns results directly to Discord. For example:
            </p>
            <ul className="text-gray-300 space-y-2 mb-4">
              <li>• <code className="bg-gray-800 px-2 py-1 rounded">/weather</code> queries open weather APIs but doesn't log your location searches</li>
              <li>• <code className="bg-gray-800 px-2 py-1 rounded">/search</code> uses DuckDuckGo but doesn't store your search terms</li>
              <li>• <code className="bg-gray-800 px-2 py-1 rounded">/stock</code> fetches financial data but doesn't track your portfolio interests</li>
              <li>• <code className="bg-gray-800 px-2 py-1 rounded">/yt</code> searches through Piped but doesn't log your viewing preferences</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">Third-Party Services</h2>
            <p className="text-gray-300 mb-4">
              Clearway integrates with several external APIs to provide its functionality. These services have their own privacy policies:
            </p>
            <ul className="text-gray-300 space-y-2 mb-4">
              <li>• <strong>DuckDuckGo:</strong> Web search (known for privacy-focused search)</li>
              <li>• <strong>Piped:</strong> YouTube search (privacy-focused YouTube frontend)</li>
              <li>• <strong>Open-Meteo:</strong> Weather data (open-source weather API)</li>
              <li>• <strong>Yahoo Finance:</strong> Stock market data</li>
              <li>• <strong>Wikipedia API:</strong> Encyclopedia searches</li>
              <li>• <strong>Dictionary API:</strong> Word definitions</li>
              <li>• <strong>Dog/Cat APIs:</strong> Random pet pictures</li>
            </ul>
            <p className="text-gray-300">
              While we don't control these third-party services, we've chosen privacy-conscious providers where possible.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">Discord Bot Permissions</h2>
            <p className="text-gray-300 mb-4">
              To function properly, Clearway requires certain Discord permissions that allow it to:
            </p>
            <ul className="text-gray-300 space-y-2 mb-4">
              <li>• Read and send messages (for command responses)</li>
              <li>• View server members and their roles (for role management features)</li>
              <li>• Manage roles (for the notification role picker)</li>
              <li>• Delete messages (for the purge moderation command)</li>
              <li>• View user presence information (online status, activities)</li>
            </ul>
            <p className="text-gray-300 mb-4">
              <strong>Important:</strong> Having these permissions doesn't mean we store the data we can access. All information is processed in real-time for immediate responses and then discarded.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">Children's Privacy</h2>
            <p className="text-gray-300 mb-4">
              Our service is designed to be safe for users of all ages. Since we don't collect any personal information, we don't have special procedures for children under 13, as there's no data collection that would trigger COPPA requirements.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">Changes to This Policy</h2>
            <p className="text-gray-300 mb-4">
              We may update this Privacy Policy from time to time. Any changes will be posted on this page with an updated date. Since we don't have your contact information, we can't notify you directly of changes.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mb-4">Contact Information</h2>
            <p className="text-gray-300">
              If you have questions about this Privacy Policy, you can contact us at: <a href="mailto:support@heysonder.xyz" className="text-blue-400 hover:text-blue-300">support@heysonder.xyz</a>
            </p>
          </section>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-gray-800 bg-gray-900/50 backdrop-blur-xl">
        <div className="max-w-4xl mx-auto px-6 py-8">
          <div className="text-center text-gray-400">
            <p>© 2024 Clearway Discord Bot. Contact: support@heysonder.xyz</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
