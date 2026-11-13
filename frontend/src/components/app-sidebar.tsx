import {
	Link,
	useNavigate,
	useRouteContext,
	useRouterState,
} from "@tanstack/react-router";
import { House, LogOut, UserRound, UtensilsCrossed } from "lucide-react";
import { toast } from "sonner";
import {
	Sidebar,
	SidebarContent,
	SidebarFooter,
	SidebarGroup,
	SidebarGroupContent,
	SidebarHeader,
	SidebarMenu,
	SidebarMenuButton,
	SidebarMenuItem,
} from "#/components/ui/sidebar";
import { useLogout } from "#/lib/api/auth";
import { getErrorMessage } from "#/lib/api/client";

const NAV_ITEMS = [
	{ title: "Home", to: "/", icon: House },
	{ title: "Profile", to: "/profile", icon: UserRound },
] as const;

export function AppSidebar() {
	const { user } = useRouteContext({ from: "/_app" });
	const pathname = useRouterState({ select: (s) => s.location.pathname });
	const navigate = useNavigate();
	const logout = useLogout();

	const handleLogout = () =>
		logout.mutate(undefined, {
			onSuccess: () => navigate({ to: "/login" }),
			onError: (error) =>
				toast.error("Couldn't log out", {
					description: getErrorMessage(error),
				}),
		});

	return (
		<Sidebar collapsible="icon">
			<SidebarHeader>
				<SidebarMenu>
					<SidebarMenuItem>
						<SidebarMenuButton size="lg" asChild>
							<Link to="/">
								<span className="flex aspect-square size-8 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground">
									<UtensilsCrossed className="size-4" />
								</span>
								<div className="grid text-left leading-tight">
									<span className="font-semibold">Shawarma Bot</span>
									<span className="truncate text-muted-foreground text-xs">
										{user.name}
									</span>
								</div>
							</Link>
						</SidebarMenuButton>
					</SidebarMenuItem>
				</SidebarMenu>
			</SidebarHeader>

			<SidebarContent>
				<SidebarGroup>
					<SidebarGroupContent>
						<SidebarMenu>
							{NAV_ITEMS.map((item) => (
								<SidebarMenuItem key={item.to}>
									<SidebarMenuButton
										asChild
										isActive={pathname === item.to}
										tooltip={item.title}
									>
										<Link to={item.to}>
											<item.icon />
											<span>{item.title}</span>
										</Link>
									</SidebarMenuButton>
								</SidebarMenuItem>
							))}
						</SidebarMenu>
					</SidebarGroupContent>
				</SidebarGroup>
			</SidebarContent>

			<SidebarFooter>
				<SidebarMenu>
					<SidebarMenuItem>
						<SidebarMenuButton
							tooltip="Log out"
							onClick={handleLogout}
							disabled={logout.isPending}
						>
							<LogOut />
							<span>Log out</span>
						</SidebarMenuButton>
					</SidebarMenuItem>
				</SidebarMenu>
			</SidebarFooter>
		</Sidebar>
	);
}
