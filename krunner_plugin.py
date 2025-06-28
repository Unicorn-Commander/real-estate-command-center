class PlasmaIntegration(QObject):
    # ... existing code ...

    def create_krunner_plugin(self):
        # Create KRunner plugin directory
        plugin_dir = Path.home() / ".local/share/krunner/plugins"
        plugin_dir.mkdir(parents=True, exist_ok=True)
        
        # Create .desktop file
        with (plugin_dir / "uc1_realestate.desktop").open("w") as f:
            f.write(f"""[Desktop Entry]
Type=Service
X-KDE-ServiceTypes=KRunner/Plugin
X-KDE-Library=plasmaprovider_uc1_realestate
X-KDE-PluginInfo-Author=Unicorn Commander
X-KDE-PluginInfo-Email=support@unicorncommander.com
X-KDE-PluginInfo-Name=UC-1 Real Estate
X-KDE-PluginInfo-Version=1.0
X-KDE-PluginInfo-Website=https://unicorncommander.com
X-KDE-PluginInfo-Category=Real Estate
X-KDE-PluginInfo-EnabledByDefault=true
X-KDE-PluginInfo-License=GPL
X-KDE-PluginInfo-Name[en_US]=UC-1 Real Estate Commander
""")
        
        # Create C++ plugin stub (would need compilation)
        # This is a placeholder - actual implementation requires C++/Qt plugin