# Prepares the Capacitor-generated Xcode project for an unattended CI build.
# Plain Ruby on top of the xcodeproj gem (a fastlane dependency), so it can be
# tested without fastlane:  ruby -r ./fastlane/ios_project.rb -e '...'
require "xcodeproj"

module MakuIosProject
  module_function

  def open_target(project_path, target_name)
    project = Xcodeproj::Project.open(project_path)
    target = project.targets.find { |t| t.name == target_name }
    raise "Xcode target '#{target_name}' not found in #{project_path}" unless target

    [project, target]
  end

  # Xcode only creates schemes when a person opens the project, so a fresh
  # `npx cap add ios` on a CI machine has none. Write a shared "App" scheme
  # that xcodebuild / gym can find. Returns true when a scheme was written.
  def ensure_shared_scheme(project_path, scheme_name: "App", target_name: "App")
    scheme_file = File.join(Xcodeproj::XCScheme.shared_data_dir(project_path), "#{scheme_name}.xcscheme")
    return false if File.exist?(scheme_file)

    _project, target = open_target(project_path, target_name)
    scheme = Xcodeproj::XCScheme.new
    scheme.configure_with_targets(target, nil, launch_target: true)
    scheme.save_as(project_path, scheme_name, true)
    true
  end

  # App Store builds must carry aps-environment=production (the generated
  # entitlements file says "development" for local debugging). Returns true
  # when the file was changed.
  def use_production_push_environment(project_path, group_name: "App")
    file = File.join(File.dirname(project_path), group_name, "App.entitlements")
    return false unless File.exist?(file)

    src = File.read(file)
    out = src.sub(%r{(<key>aps-environment</key>\s*<string>)development(</string>)}, '\1production\2')
    File.write(file, out) unless out == src
    out != src
  end

  # Adds ios/App/App/GoogleService-Info.plist to the App target's resources,
  # which is what "drag it into Xcode" does by hand. Without it Firebase push
  # stays disabled (the app still runs). Returns :added, :present or :missing.
  def add_google_service_plist(project_path, target_name: "App", group_name: "App")
    plist = File.expand_path(File.join(File.dirname(project_path), group_name, "GoogleService-Info.plist"))
    return :missing unless File.exist?(plist)

    project, target = open_target(project_path, target_name)
    group = project.main_group.children.find { |g| g.respond_to?(:display_name) && g.display_name == group_name }
    raise "Xcode group '#{group_name}' not found" unless group
    return :present if group.files.any? { |f| File.basename(f.path.to_s) == "GoogleService-Info.plist" }

    ref = group.new_reference(plist)
    target.resources_build_phase.add_file_reference(ref, true)
    project.save
    :added
  end
end
