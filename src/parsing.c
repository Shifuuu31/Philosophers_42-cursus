/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   parsing.c                                          :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: asaadane <asaadane@student.42.fr>          +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2024/01/02 23:03:53 by asaadane          #+#    #+#             */
/*   Updated: 2026/11/18 19:43:00 by asaadane         ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "philo.h"

// Error messages based on error codes and arguments
static int	err_msg(int code, int args_num)
{
	if (!code)
		printf("Error : Incorrect number of arguments (expected 4) got %d\n",
			args_num);
	else if (code == 1)
	{
		printf("Error : All arguments must be numbers.\n");
		printf("Format : n_philo t_die t_eat t_sleep nbr_meals[optinal]\n");
	}
	else if (code == 2)
		printf("Error : None of the parameters can be less or equal to 0\n");
	else if (code == 3)
		printf("Error : Malloc error\n");
	return (0);
}

// Initialize mutexes and state per philosopher
static void	init_data(t_philo *target)
{
	int	i;

	i = -1;
	while (++i < target->n_philo)
		pthread_mutex_init(&target->forks[i], NULL);
	pthread_mutex_init(&target->sync, NULL);
	i = -1;
	while (++i < target->n_philo)
	{
		target->philo[i].id = i + 1;
		target->philo[i].n_philo = target->n_philo;
		if (!i)
			target->philo[i].left_fork = &target->forks[target->n_philo - 1];
		else
			target->philo[i].left_fork = &target->forks[i - 1];
		target->philo[i].right_fork = &target->forks[i];
		target->philo[i].sync = &target->sync;
		target->philo[i].t_eat = target->t_eat;
		target->philo[i].t_sleep = target->t_sleep;
		target->philo[i].last_meal = 0;
		target->philo[i].eating_time = 0;
	}
}

// Load parsed values into main structure and allocate arrays
static void	load_info_to_struct(char **args, t_philo *target)
{
	target->n_philo = ft_atoi(args[0]);
	target->t_die = ft_atoi(args[1]);
	target->t_eat = ft_atoi(args[2]);
	target->t_sleep = ft_atoi(args[3]);
	if (args[4])
	{
		target->nbr_meals = ft_atoi(args[4]);
		target->philo_eaft_time = TRUE;
	}
	else
	{
		target->nbr_meals = 1;
		target->philo_eaft_time = FALSE;
	}
	target->forks = NULL;
	target->philo = NULL;
	if (target->nbr_meals <= 0 || target->n_philo <= 0
		|| target->t_die <= 0 || target->t_eat <= 0 || target->t_sleep <= 0)
		return ;
	target->forks = (pthread_mutex_t *)
		malloc(target->n_philo * sizeof(pthread_mutex_t));
	target->philo = (t_info *)
		malloc(target->n_philo * sizeof(t_info));
	if (!target->forks || !target->philo)
		return ;
	init_data(target);
}

// Parse command line arguments and initialize structures
int	parsing(char **args, int args_num, t_philo *target)
{
	int	j;
	int	i;

	if (args_num < 4 || args_num > 5)
		return (err_msg(0, args_num));
	i = 0;
	while (++i < args_num + 1)
	{
		j = 0;
		if (args[i][j] == '+')
			j++;
		if (!args[i][j])
			return (err_msg(1, 0));
		while (args[i][j])
		{
			if (!ft_isdigit(args[i][j]))
				return (err_msg(1, 0));
			j++;
		}
	}
	load_info_to_struct(args + 1, target);
	if (target->nbr_meals <= 0 || target->n_philo <= 0
		|| target->t_die <= 0 || target->t_eat <= 0 || target->t_sleep <= 0)
		return (err_msg(2, 0));
	if (!target->forks || !target->philo)
		return (err_msg(3, 0));
	return (1);
}
